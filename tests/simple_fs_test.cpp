#include <gtest/gtest.h>

#include "oscope/filesystem/simple_fs.hpp"

using namespace oscope::filesystem;

TEST(SimpleFilesystemTest, FormatsAndCreatesRootDirectory) {
    SimpleFilesystem fs(32, 512);
    auto status = fs.get_status();
    EXPECT_EQ(status.total_blocks, 32);
    EXPECT_EQ(status.free_blocks, 32);
    EXPECT_EQ(status.used_blocks, 0);
    EXPECT_EQ(status.directory_count, 1); // root '/'
    EXPECT_EQ(status.file_count, 0);

    auto root_entries = fs.list_directory("/");
    ASSERT_TRUE(root_entries.has_value());
    EXPECT_TRUE(root_entries->empty());
}

TEST(SimpleFilesystemTest, CreatesDirectoriesAndListsHierarchy) {
    SimpleFilesystem fs(32, 512);
    EXPECT_TRUE(fs.create_directory("/home"));
    EXPECT_TRUE(fs.create_directory("/home/user"));
    EXPECT_FALSE(fs.create_directory("/nonexistent/sub")); // parent doesn't exist

    auto root_entries = fs.list_directory("/");
    ASSERT_TRUE(root_entries.has_value());
    EXPECT_EQ(root_entries->size(), 1u);
    EXPECT_EQ((*root_entries)[0].name, "home");
    EXPECT_TRUE((*root_entries)[0].is_directory);

    auto home_entries = fs.list_directory("/home");
    ASSERT_TRUE(home_entries.has_value());
    EXPECT_EQ(home_entries->size(), 1u);
    EXPECT_EQ((*home_entries)[0].name, "user");
}

TEST(SimpleFilesystemTest, AllocatesFilesContiguously) {
    SimpleFilesystem fs(32, 512);
    // 1500 bytes -> needs 3 blocks of 512 bytes
    EXPECT_TRUE(fs.create_file("/data.bin", 1500, AllocationStrategy::Contiguous));

    auto meta = fs.get_metadata("/data.bin");
    ASSERT_TRUE(meta.has_value());
    EXPECT_EQ(meta->block_count, 3);
    EXPECT_EQ(meta->allocated_blocks.size(), 3u);
    EXPECT_EQ(meta->allocated_blocks[0], 0);
    EXPECT_EQ(meta->allocated_blocks[1], 1);
    EXPECT_EQ(meta->allocated_blocks[2], 2);

    auto status = fs.get_status();
    EXPECT_EQ(status.used_blocks, 3);
    EXPECT_EQ(status.free_blocks, 29);
}

TEST(SimpleFilesystemTest, AllocatesFilesWithIndexedStrategy) {
    SimpleFilesystem fs(32, 512);
    // 1000 bytes -> 2 data blocks + 1 index block = 3 blocks
    EXPECT_TRUE(fs.create_file("/indexed.txt", 1000, AllocationStrategy::Indexed));

    auto meta = fs.get_metadata("/indexed.txt");
    ASSERT_TRUE(meta.has_value());
    EXPECT_EQ(meta->strategy, AllocationStrategy::Indexed);
    EXPECT_GE(meta->index_block, 0);
    EXPECT_EQ(meta->allocated_blocks.size(), 2u);
    EXPECT_EQ(meta->block_count, 3);

    auto status = fs.get_status();
    EXPECT_EQ(status.used_blocks, 3);
}

TEST(SimpleFilesystemTest, DemonstratesExternalFragmentationUnderContiguousAllocation) {
    // 6 blocks total
    SimpleFilesystem fs(6, 512);
    EXPECT_TRUE(fs.create_file("/f1", 512, AllocationStrategy::Contiguous)); // block 0
    EXPECT_TRUE(fs.create_file("/f2", 512, AllocationStrategy::Contiguous)); // block 1
    EXPECT_TRUE(fs.create_file("/f3", 512, AllocationStrategy::Contiguous)); // block 2
    EXPECT_TRUE(fs.create_file("/f4", 512, AllocationStrategy::Contiguous)); // block 3

    // Delete f1 and f3, creating fragmented free blocks: block 0 (free), block 1 (used), block 2 (free), block 3 (used), blocks 4,5 (free)
    EXPECT_TRUE(fs.delete_file("/f1"));
    EXPECT_TRUE(fs.delete_file("/f3"));

    // Total free blocks = 4 (blocks 0, 2, 4, 5).
    // Try to allocate 3 contiguous blocks (1500 bytes).
    // The largest contiguous free chunk is 2 (blocks 4, 5).
    // Contiguous allocation MUST FAIL due to external fragmentation!
    EXPECT_FALSE(fs.create_file("/big_contiguous", 1500, AllocationStrategy::Contiguous));

    // But Linked allocation DOES NOT require contiguous blocks and MUST SUCCEED!
    EXPECT_TRUE(fs.create_file("/big_linked", 1500, AllocationStrategy::Linked));
    auto meta = fs.get_metadata("/big_linked");
    ASSERT_TRUE(meta.has_value());
    EXPECT_EQ(meta->allocated_blocks.size(), 3u);
}
