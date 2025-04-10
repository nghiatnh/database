#include <gtest/gtest.h>

class BTreeTest : public ::testing::Test {
 protected:
  void test_insert();
  void test_remove();
};

void BTreeTest::test_insert() {}

void BTreeTest::test_remove() {}

// Call your member functions from gTest wrappers
TEST_F(BTreeTest, Insert) { test_insert(); }

TEST_F(BTreeTest, Remove) { test_remove(); }