import sqlite3
from sqlite3 import Error

#db_file = '/home/GB/guild_warehouse.db'
db_file = 'D:\\sqlite\\guild_warehouse.db'

create_res = 'create table if not exists g_stock_res (user_id number, res_id varchar2(4), res_name varchar2(128), amount number, version varchar2(3))'
create_alch = 'create table if not exists g_stock_alch (user_id number, res_id varchar2(4), res_name varchar2(128), amount number, version varchar2(3))'
create_misc = 'create table if not exists g_stock_misc (user_id number, res_id varchar2(4), res_name varchar2(128), amount number, version varchar2(3))'
create_rec = 'create table if not exists g_stock_rec (user_id number, res_id varchar2(4), res_name varchar2(128), amount number, version varchar2(3))'
create_parts = 'create table if not exists g_stock_parts (user_id number, res_id varchar2(4), res_name varchar2(128), amount number, version varchar2(3))'
create_other = 'create table if not exists g_stock_other (user_id number, res_id varchar2(4), res_name varchar2(128), amount number, version varchar2(3))'

#create master tables
create_res_m = 'create table if not exists g_stock_res_m as select res_id, res_name from g_stock_res where 1=0'
create_alch_m = 'create table if not exists g_stock_alch_m as select res_id, res_name from g_stock_alch where 1=0'
create_misc_m = 'create table if not exists g_stock_misc_m as select res_id, res_name from g_stock_misc where 1=0'
create_rec_m = 'create table if not exists g_stock_rec_m as select res_id, res_name from g_stock_rec where 1=0'
create_parts_m = 'create table if not exists g_stock_parts_m as select res_id, res_name from g_stock_parts where 1=0'
create_other_m = 'create table if not exists g_stock_other_m as select res_id, res_name from g_stock_other where 1=0'
create_temp = 'create table if not exists g_temp as select user_id, res_id, res_name, amount from g_stock_res where 1=0'

def create_connection(db_file):
    return sqlite3.connect(db_file)

def create_tab(conn, sql):
    c = conn.cursor()
    try:
        c.execute(sql)
        print('Table ' + sql[sql.find('g_'):sql.find(' ', sql.find('g_'))] + ' is created') # get name of table from sql string
        conn.commit()
    except Error as e1:
        print(e1)

def insert_row(conn, sql):
    pass

def main():
    conn = create_connection(db_file)
    create_tab(conn, create_res)
    create_tab(conn, create_alch)
    create_tab(conn, create_misc)
    create_tab(conn, create_rec)
    create_tab(conn, create_parts)
    create_tab(conn, create_other)
    create_tab(conn, create_res_m)
    create_tab(conn, create_alch_m)
    create_tab(conn, create_misc_m)
    create_tab(conn, create_rec_m)
    create_tab(conn, create_parts_m)
    create_tab(conn, create_other_m)
    create_tab(conn, create_temp)

if __name__ == '__main__':
    main()