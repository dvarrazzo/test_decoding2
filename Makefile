MODULE_big = test_decoding2
OBJS = test_decoding.o

PG_CONFIG = pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)
