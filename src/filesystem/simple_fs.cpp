#include "oscope/filesystem/simple_fs.hpp"

#include <algorithm>

namespace oscope::filesystem {

namespace {

std::pair<std::string, std::string> split_path(const std::string& path) {
    if (path.empty() || path == "/") {
        return {"", "/"};
    }
    std::string clean = path;
    if (clean.front() != '/') {
        clean = "/" + clean;
    }
    while (clean.size() > 1 && clean.back() == '/') {
        clean.pop_back();
    }
    size_t last_slash = clean.find_last_of('/');
    if (last_slash == 0) {
        return {"/", clean.substr(1)};
    }
    return {clean.substr(0, last_slash), clean.substr(last_slash + 1)};
}

} // namespace

SimpleFilesystem::SimpleFilesystem(int total_blocks, int block_size)
    : total_blocks_(total_blocks > 0 ? total_blocks : 64),
      block_size_(block_size > 0 ? block_size : 512),
      bitmap_(static_cast<size_t>(total_blocks_), false) {
    format();
}

void SimpleFilesystem::format() {
    std::fill(bitmap_.begin(), bitmap_.end(), false);
    inodes_.clear();
    next_inode_id_ = 1;

    // Create root inode
    FileMetadata root;
    root.inode_id = 0;
    root.name = "/";
    root.path = "/";
    root.is_directory = true;
    root.size_bytes = 0;
    inodes_.push_back(root);
}

int SimpleFilesystem::allocate_contiguous_blocks(int count, std::vector<int>& out_blocks) {
    out_blocks.clear();
    if (count <= 0) return 0;

    int consecutive = 0;
    int start_idx = -1;

    for (int i = 0; i < total_blocks_; ++i) {
        if (!bitmap_[static_cast<size_t>(i)]) {
            if (consecutive == 0) start_idx = i;
            consecutive++;
            if (consecutive == count) {
                // Found contiguous chunk!
                for (int b = start_idx; b < start_idx + count; ++b) {
                    bitmap_[static_cast<size_t>(b)] = true;
                    out_blocks.push_back(b);
                }
                return start_idx;
            }
        } else {
            consecutive = 0;
            start_idx = -1;
        }
    }
    return -1; // Allocation failed (e.g. external fragmentation)
}

int SimpleFilesystem::allocate_linked_blocks(int count, std::vector<int>& out_blocks) {
    out_blocks.clear();
    if (count <= 0) return 0;

    // Check if enough free blocks exist
    int free_count = 0;
    for (bool bit : bitmap_) {
        if (!bit) free_count++;
    }
    if (free_count < count) return -1;

    for (int i = 0; i < total_blocks_ && static_cast<int>(out_blocks.size()) < count; ++i) {
        if (!bitmap_[static_cast<size_t>(i)]) {
            bitmap_[static_cast<size_t>(i)] = true;
            out_blocks.push_back(i);
        }
    }
    return out_blocks.empty() ? -1 : out_blocks.front();
}

int SimpleFilesystem::allocate_indexed_blocks(int count, int& out_index_block, std::vector<int>& out_blocks) {
    out_blocks.clear();
    out_index_block = -1;
    if (count <= 0) return 0;

    // Needs 1 block for the index block + count data blocks
    int needed = count + 1;
    int free_count = 0;
    for (bool bit : bitmap_) {
        if (!bit) free_count++;
    }
    if (free_count < needed) return -1;

    // Allocate index block first
    for (int i = 0; i < total_blocks_; ++i) {
        if (!bitmap_[static_cast<size_t>(i)]) {
            bitmap_[static_cast<size_t>(i)] = true;
            out_index_block = i;
            break;
        }
    }

    // Allocate data blocks
    for (int i = 0; i < total_blocks_ && static_cast<int>(out_blocks.size()) < count; ++i) {
        if (!bitmap_[static_cast<size_t>(i)]) {
            bitmap_[static_cast<size_t>(i)] = true;
            out_blocks.push_back(i);
        }
    }
    return out_index_block;
}

void SimpleFilesystem::free_blocks(const std::vector<int>& blocks) {
    for (int b : blocks) {
        if (b >= 0 && b < total_blocks_) {
            bitmap_[static_cast<size_t>(b)] = false;
        }
    }
}

bool SimpleFilesystem::create_directory(const std::string& path) {
    auto [parent, name] = split_path(path);
    if (name.empty() || name == "/") return false;

    // Check if target already exists
    for (const auto& in : inodes_) {
        if (in.path == path) return false;
    }

    // Check if parent directory exists
    bool parent_exists = false;
    for (const auto& in : inodes_) {
        if (in.path == parent && in.is_directory) {
            parent_exists = true;
            break;
        }
    }
    if (!parent_exists) return false;

    FileMetadata dir;
    dir.inode_id = next_inode_id_++;
    dir.name = name;
    dir.path = (parent == "/" ? "/" + name : parent + "/" + name);
    dir.is_directory = true;
    dir.size_bytes = 0;
    inodes_.push_back(dir);
    return true;
}

std::optional<std::vector<DirectoryEntry>> SimpleFilesystem::list_directory(const std::string& path) const {
    std::string clean = path;
    if (clean.empty()) clean = "/";
    if (clean.front() != '/') clean = "/" + clean;
    while (clean.size() > 1 && clean.back() == '/') clean.pop_back();

    bool dir_exists = false;
    for (const auto& in : inodes_) {
        if (in.path == clean && in.is_directory) {
            dir_exists = true;
            break;
        }
    }
    if (!dir_exists) return std::nullopt;

    std::vector<DirectoryEntry> entries;
    for (const auto& in : inodes_) {
        if (in.path == clean) continue;
        auto [p, n] = split_path(in.path);
        if (p == clean) {
            DirectoryEntry de;
            de.inode_id = in.inode_id;
            de.name = in.name;
            de.is_directory = in.is_directory;
            de.size_bytes = in.size_bytes;
            entries.push_back(de);
        }
    }
    return entries;
}

bool SimpleFilesystem::remove_directory(const std::string& path) {
    if (path.empty() || path == "/") return false; // cannot remove root
    auto [parent, name] = split_path(path);
    std::string clean = (parent == "/" ? "/" + name : parent + "/" + name);

    // Cannot remove if not empty
    auto listing = list_directory(clean);
    if (!listing || !listing->empty()) {
        return false;
    }

    auto it = std::find_if(inodes_.begin(), inodes_.end(), [&](const FileMetadata& m) {
        return m.path == clean && m.is_directory;
    });

    if (it != inodes_.end()) {
        inodes_.erase(it);
        return true;
    }
    return false;
}

bool SimpleFilesystem::create_file(
    const std::string& path,
    uint64_t size_bytes,
    AllocationStrategy strategy) {

    auto [parent, name] = split_path(path);
    if (name.empty() || name == "/") return false;
    std::string clean = (parent == "/" ? "/" + name : parent + "/" + name);

    // Check if file already exists
    for (const auto& in : inodes_) {
        if (in.path == clean) return false;
    }

    // Verify parent directory
    bool parent_exists = false;
    for (const auto& in : inodes_) {
        if (in.path == parent && in.is_directory) {
            parent_exists = true;
            break;
        }
    }
    if (!parent_exists) return false;

    int blocks_needed = static_cast<int>((size_bytes + static_cast<uint64_t>(block_size_) - 1) / static_cast<uint64_t>(block_size_));
    if (blocks_needed == 0) blocks_needed = 1;

    std::vector<int> allocated;
    int start_block = -1;
    int index_block = -1;

    if (strategy == AllocationStrategy::Contiguous) {
        start_block = allocate_contiguous_blocks(blocks_needed, allocated);
        if (start_block < 0) return false; // Not enough contiguous space
    } else if (strategy == AllocationStrategy::Linked) {
        start_block = allocate_linked_blocks(blocks_needed, allocated);
        if (start_block < 0) return false;
    } else if (strategy == AllocationStrategy::Indexed) {
        int idx = allocate_indexed_blocks(blocks_needed, index_block, allocated);
        if (idx < 0) return false;
        start_block = index_block;
    }

    FileMetadata file;
    file.inode_id = next_inode_id_++;
    file.name = name;
    file.path = clean;
    file.is_directory = false;
    file.size_bytes = size_bytes;
    file.strategy = strategy;
    file.start_block = start_block;
    file.index_block = index_block;
    file.block_count = static_cast<int>(allocated.size()) + (index_block >= 0 ? 1 : 0);
    file.allocated_blocks = allocated;
    inodes_.push_back(file);

    return true;
}

bool SimpleFilesystem::delete_file(const std::string& path) {
    auto [parent, name] = split_path(path);
    std::string clean = (parent == "/" ? "/" + name : parent + "/" + name);

    auto it = std::find_if(inodes_.begin(), inodes_.end(), [&](const FileMetadata& m) {
        return m.path == clean && !m.is_directory;
    });

    if (it != inodes_.end()) {
        std::vector<int> to_free = it->allocated_blocks;
        if (it->index_block >= 0) {
            to_free.push_back(it->index_block);
        }
        free_blocks(to_free);
        inodes_.erase(it);
        return true;
    }
    return false;
}

std::optional<FileMetadata> SimpleFilesystem::get_metadata(const std::string& path) const {
    auto [parent, name] = split_path(path);
    std::string clean = (parent == "/" ? "/" + name : parent + "/" + name);

    for (const auto& in : inodes_) {
        if (in.path == clean) {
            return in;
        }
    }
    return std::nullopt;
}

FilesystemStatus SimpleFilesystem::get_status() const {
    FilesystemStatus status;
    status.total_blocks = total_blocks_;
    status.block_size = block_size_;
    status.block_bitmap = bitmap_;

    int used = 0;
    for (bool bit : bitmap_) {
        if (bit) used++;
    }
    status.used_blocks = used;
    status.free_blocks = total_blocks_ - used;

    int files = 0;
    int dirs = 0;
    for (const auto& in : inodes_) {
        if (in.is_directory) dirs++;
        else files++;
    }
    status.file_count = files;
    status.directory_count = dirs;

    return status;
}

} // namespace oscope::filesystem
