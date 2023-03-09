CREATE TABLE bot_user(
    bot_user_id INT PRIMARY KEY, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    telegram_id BIGINT NOY NULL
);

CREATE TABLE product(
    product_id INT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMPNOT NOT NULL,
    date_prod DATE,
    date_exp DATE,
    label_path VARCHAR(200),
    bot_user_id INT NOT NULL,
    FOREIGN KEY (bot_user_id) REFERENCES user (bot_user_id) 
);
