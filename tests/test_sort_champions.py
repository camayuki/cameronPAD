import unittest

class TestSortChampions(unittest.TestCase):
    def setUp(self):
        self.champions = [
            {'name': 'Ahri', 'info': {'attack': 3, 'defense': 4, 'magic': 8, 'difficulty': 5}},
            {'name': 'Zed', 'info': {'attack': 9, 'defense': 2, 'magic': 1, 'difficulty': 7}},
            {'name': 'Lux', 'info': {'attack': 2, 'defense': 3, 'magic': 9, 'difficulty': 4}},
        ]

    def test_sort_by_name_ascending(self):
        sorted_champions = sorted(self.champions, key=lambda x: x['name'])
        self.assertEqual([champ['name'] for champ in sorted_champions], ['Ahri', 'Lux', 'Zed'])

    def test_sort_by_name_descending(self):
        sorted_champions = sorted(self.champions, key=lambda x: x['name'], reverse=True)
        self.assertEqual([champ['name'] for champ in sorted_champions], ['Zed', 'Lux', 'Ahri'])

    def test_sort_by_attack_descending(self):
        sorted_champions = sorted(self.champions, key=lambda x: x['info']['attack'], reverse=True)
        self.assertEqual([champ['name'] for champ in sorted_champions], ['Zed', 'Ahri', 'Lux'])

if __name__ == '__main__':
    unittest.main()