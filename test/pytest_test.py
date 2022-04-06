import os

# local imports
import modb


class TestClass:

    @classmethod
    def setup_class(cls):
        cls.filename = './tmp/a'
        cls.db = modb.Database(cls.filename)
        cls.node = cls.db.connect()

    @classmethod
    def teardown_class(cls):
        cls.db.close()
        os.remove(cls.filename)

    def test_insert(self):
        for c in 'abcdefghijklmn':
            self.node.insert(c, f'{c}_value')

    def test_search(self):
        for c in 'abcdefghijklmn':
            assert self.node.search(c).get() == f'{c}_value'

    def test_create_subtree(self):
        self.node.create('sub')

    def test_search_subtree(self):
        sub = self.node.search('sub').get()

    def test_insert_to_subtree(self):
        sub = self.node.search('sub').get()
        sub.insert('sub_a', 'sub_a_value')

    def test_search_in_subtree(self):
        sub = self.node.search('sub').get()
        assert sub.search('sub_a').get() == 'sub_a_value'
