COLUNAS_TEMPORADA = "Periodo"
COLUNAS_JOGO = "Codigo_temporada_jogo, Data, Codigo_time_mandante, Codigo_time_visitante, Pontuacao_time_mandante, Pontuacao_time_visitante"
COLUNAS_EQUIPE = "Nome"
COLUNAS_JOGADOR = "Codigo_equipe_atual, idade, Nome"
COLUNAS_INFORMACOES_JOGO_JOGADOR = "Codigo_jogador_fk, Codigo_jogo_fk, Tempo_em_quadra, Arremessos, Arremessos_certos, Tres_pontos, Tres_pontos_certos, Lance_livre, Lance_livre_certos, Rebotes_ofensivos, Rebotes_defensivos, Assistencias, Roubos, Bloqueios, Bolas_perdidas, Faltas, Pontos, Contribuicao"
INFORMACAO_JOGO = {"MP": "Tempo_em_quadra", "FG": "Arremessos_certos", "FGA": "Arremessos", 
                   "3P": "Tres_pontos", "3PA": "Tres_pontos_certos", "FT":"Lance_livre_certos", "FTA": "Lance_livre",
                   "ORB": "Rebotes_ofensivos", "DRB":"Rebotes_defensivos", "AST": "Assistencias", "STL": "Roubos", 
                   "BLK": "Bloqueios", "TOV": "Bolas_perdidas", "PF": "Faltas", "PTS": "Pontos", "+/-": "Contribuicao"}
TIMES = {
    "Atlanta Hawks":"ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BRK",
    "New York Knicks": "NYK",
    "Philadelphia 76ers": "PHI",
    "Toronto Raptors": "TOR",
    "Chicago Bulls": "CHI",
    "Minnesota Timberwolves": "MIN",
    "Houston Rockets":"HOU",
    "Orlando Magic":"ORL",
    "Detroit Pistons":"DET",
    "Cleveland Cavaliers": "CLE",
    "Indiana Pacers":"IND",
    "Milwaukee Bucks": "MIL",
    "Denver Nuggets": "DEN",
    "Oklahoma City Thunder": "OKC",
    "Portland Trail Blazers": "POR",
    "Utah Jazz": "UTA",
    "Golden State Warriors": "GSW",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Phoenix Suns": "PHO",
    "Sacramento Kings": "SAC",
    "Charlotte Hornets": "CHO",
    "Miami Heat": "MIA",
    "Washington Wizards": "WAS",
    "Dallas Mavericks": "DAL",
    "Memphis Grizzlies": "MEM",
    "New Orleans Pelicans": "NOP",
    "San Antonio Spurs": "SAS"
}