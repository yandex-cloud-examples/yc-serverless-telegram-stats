clickhouse client --host $TF_VAR_CH_HOST \
                  --secure \
                  --user $TF_VAR_CH_USER_NAME \
                  --database $TF_VAR_CH_DB_NAME \
                  --port 9440 \
                  --password $TF_VAR_CH_PASSWORD --queries-file create_tables.sql
