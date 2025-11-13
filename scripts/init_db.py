#!/usr/bin/env python3
from models.database import init_db

if __name__ == '__main__':
    init_db()
    print('Database initialized (./data/quant.db)')
