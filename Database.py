import os

import rrdtool as rrd


class Database:

    def __init__(self, file):
        self.db = file

    @classmethod
    def create(cls, name, step, data_srcs, archives):
        if os.path.isfile(name):
            raise FileExistsError

        if not name.endswith('.rrd'):
            name += '.rrd'

        # Create database
        rrd.create(name, '--step', str(step), data_srcs, archives)
        # Load database
        return Database.load(name)

    @classmethod
    def load(cls, file):
        if not os.path.isfile(file):
            raise FileNotFoundError
        return Database(file)

    # =============================
    def add_data(self, data_list, time='N'):
        update_list = ""
        for data in data_list:
            update_list += ':' + str(data)
        rrd.update(self.db, time + update_list)

    def get_data(self, start_time=None, end_time='now'):
        time_parameters = ['--end', end_time]
        if start_time is not None:
            time_parameters += '--start'
            time_parameters += str(start_time)

        ret = {}
        for cf in ('LAST', 'AVERAGE', 'MIN', 'MAX'):
            result = rrd.fetch(self.db, cf)
            ret[cf] = self._parse_result(result)

        return ret

    # =============================
    def _parse_result(self, result):
        start, end, step = result[0]
        ds = result[1]
        rows = result[2]

        def is_row_empty(row):
            if row is None:
                return False

            for value in row:
                if value is not None:
                    return False
            return True

        # Build dict with datasource : [(timestamp, value) if value not None]
        len_rows = len(rows)
        max_idx = len_rows - 1
        result = {ds[i]: [((end - j * step), rows[max_idx - j][i])
                         for j in range(len_rows)
                         if not is_row_empty(rows[max_idx - j])]
                  for i in range(len(ds))}
        """data = [((end - i * step), rows[max_idx - i])
                for i in range(len_rows)
                if not is_row_empty(rows[max_idx - i])]"""
        return result
