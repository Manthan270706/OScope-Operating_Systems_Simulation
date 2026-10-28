#ifndef OSCOPE_FILESYSTEM_SIMPLE_FS_HPP
#define OSCOPE_FILESYSTEM_SIMPLE_FS_HPP

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace oscope::filesystem {

enum class AllocationStrategy {
    Contiguous,
    Linked,
    Indexed
};

struct FileMetadata {
    int inode_id{0};
    std::string name;
    std::string path;
    bool is_directory{false};
    uint64_t size_bytes{0};
    AllocationStrategy strategy{AllocationStrategy::Indexed};
    int index_block{-1};                // For Indexed allocation
    int start_block{-1};                // For Contiguous & Linked allocation
    int block_count{0};
    std::vector<int> allocated_blocks;  // Exact physical block IDs allocated
};

struct DirectoryEntry {
    std::string name;
    int inode_id{0};
    bool is_directory{false};
    uint64_t size_bytes{0};
};

struct FilesystemStatus {
    int total_blocks{64};
    int block_size{512};
    int free_blocks{64};
    int used_blocks{0};
    int file_count{0};
    int directory_count{1}; // root '/'
    std::vector<bool> block_bitmap; // true = allocated, false = free
};

class SimpleFilesystem {
public:
    explicit SimpleFilesystem(int total_blocks = 64, int block_size = 512);

    void format();

    // Directory operations
    bool create_directory(const std::string& path);
    std::optional<std::vector<DirectoryEntry>> list_directory(const std::string& path) const;
    bool remove_directory(const std::string& path);

    // File operations
    bool create_file(
        const std::string& path,
        uint64_t size_bytes,
        AllocationStrategy strategy = AllocationStrategy::Indexed);

    bool delete_file(const std::string& path);

    std::optional<FileMetadata> get_metadata(const std::string& path) const;

    // Free space & allocation inspection
    FilesystemStatus get_status() const;
    const std::vector<bool>& bitmap() const noexcept { return bitmap_; }

private:
    int allocate_contiguous_blocks(int count, std::vector<int>& out_blocks);
    int allocate_linked_blocks(int count, std::vector<int>& out_blocks);
    int allocate_indexed_blocks(int count, int& out_index_block, std::vector<int>& out_blocks);
    void free_blocks(const std::vector<int>& blocks);

    int total_blocks_{64};
    int block_size_{512};
    std::vector<bool> bitmap_; // false = free, true = allocated
    int next_inode_id_{1};

    std::vector<FileMetadata> inodes_;
};

} // namespace oscope::filesystem

#endif // OSCOPE_FILESYSTEM_SIMPLE_FS_HPP
