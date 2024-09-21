CREATE TABLE IF NOT EXISTS markets (
  market_id INT PRIMARY KEY,
  book INT[] NOT NULL, 
  price_tick INT NOT NULL,
  ask_index INT NOT NULL
);

CREATE TABLE IF NOT EXISTS position (
  telegram_user_id SERIAL PRIMARY KEY,
  size INT NOT NULL,
  notional INT NOT NULL,
  max_price INT NOT NULL,
  market_id INT NOT NULL,
  prediciton INT NOT NULL,
  timestamp TIMESTAMP NOT NULL
)

