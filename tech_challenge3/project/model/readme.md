# Documentação do Modelo de Previsão de Preços

## Escolha do Modelo

O modelo selecionado para previsão foi o **RandomForestRegressor**, devido ao seu desempenho superior nas métricas avaliadas:

- **R² (Coeficiente de Determinação):** Mede o quanto o modelo explica a variabilidade dos dados. Valores próximos de 1 indicam excelente ajuste.
- **MSE (Erro Quadrático Médio):** Avalia a média dos erros quadráticos entre valores previstos e reais. Quanto menor, melhor a performance.

## Variáveis de Entrada (X)

O modelo utiliza as seguintes variáveis como entrada:

- `temperature_2m_max` (Temperatura máxima diária a 2m)
- `temperature_2m_min` (Temperatura mínima diária a 2m)
- `wind_speed_10m_max` (Velocidade máxima do vento a 10m)
- `rain_sum` (Total de chuva diária)
- `rain` (Chuva acumulada)
- `precipitation_hours` (Horas de precipitação)
- `month` (Mês)
- `day_of_week` (Dia da semana)
- `year` (Ano)

## Variáveis de Saída (Y)

- `price_br` (Preço no Brasil)
- `price_us` (Preço nos EUA)

## Comparativo de Modelos e Desempenho

| Modelo                   | MSE        | R²     |
|--------------------------|------------|--------|
| LinearRegression         | 30527.60   | 0.4527 |
| DecisionTreeRegressor    | 12919.54   | 0.8104 |
| RandomForestRegressor    | 6486.57    | 0.9021 |
| RandomForestRegressor (refinado) | 6362.71    | 0.9033 |

O **RandomForestRegressor refinado** apresentou o melhor desempenho, sendo escolhido para o projeto.