from typing import Dict, List

class PlayerProjection:
    def __init__(self, player_data: Dict):
        self.name = player_data.get('name')
        self.team = player_data.get('team')
        self.position = player_data.get('position')
        self.stats = self._calculate_stats(player_data)
        self.value_score = self._compute_value_score()

    def _calculate_stats(self, data) -> Dict:
        return {
            'hits': (data.get('avg', 0) * data.get('ab', 0)) + (data.get('bb', 0) * 0.25),
            'home_runs': data.get('hr_rate', 0) * data.get('ab', 0),
            'strikeouts': data.get('k_rate', 0) * data.get('ab', 0),
            'rbis': data.get('rbi_rate', 0) * data.get('pa', 0),
            'walks': data.get('bb_rate', 0) * data.get('pa', 0)
        }

    def _compute_value_score(self) -> float:
        return (self.stats['hits'] * 0.3 +
                self.stats['home_runs'] * 0.4 +
                self.stats['rbis'] * 0.3) * 1.2

class BettingAnalyzer:
    def __init__(self, projections: List[PlayerProjection]):
        self.projections = projections
        self.value_plays = []
        self.arb_opportunities = []

    def analyze_odds(self, markets):
        for market in markets:
            player_proj = next((p for p in self.projections if p.name == market.get('player')), None)
            if not player_proj:
                continue
            for book in market.get('markets', []):
                implied_prob = self._convert_odds(book['odds'])
                stat_proj = player_proj.stats.get(market['type'], 0) / 100
                if stat_proj > implied_prob + 0.05:
                    self.value_plays.append({
                        'player': player_proj.name,
                        'prop': market['type'],
                        'odds': book['odds'],
                        'edge': round(stat_proj - implied_prob, 3),
                        'book': book['bookmaker']
                    })
            self._check_arbitrage(market)

    def _check_arbitrage(self, market):
        odds = [(b['bookmaker'], b['odds']) for b in market.get('markets', []) if 'odds' in b]
        for i, (book1, odds1) in enumerate(odds):
            for book2, odds2 in odds[i+1:]:
                if (odds1 > 0 and odds2 < 0) or (odds1 < 0 and odds2 > 0):
                    arb = self._calculate_arbitrage(odds1, odds2)
                    if arb > 0:
                        self.arb_opportunities.append({
                            'player': market['player'],
                            'prop': market['type'],
                            'book1': book1,
                            'book2': book2,
                            'odds1': odds1,
                            'odds2': odds2,
                            'profit': round(arb * 100, 2)
                        })

    @staticmethod
    def _convert_odds(odds: int) -> float:
        return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)

    @staticmethod
    def _calculate_arbitrage(odds1: int, odds2: int) -> float:
        p1 = BettingAnalyzer._convert_odds(odds1)
        p2 = BettingAnalyzer._convert_odds(odds2)
        return 1 - (p1 + p2) if p1 + p2 < 1 else 0
