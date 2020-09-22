import os

import rrdtool as rrd


class Datasource:

    def __init__(self, ds_name, dst, heartbeat, min='U', max='U'):
        self.name = str(ds_name)
        self.specs = str(ds_name) + ':' + str(dst) + ':' + str(heartbeat) + ':' + str(min) + ":" + str(max)

    def get_name(self):
        return self.name

    def get_complete_string(self):
        return 'DS:' + self.specs

    def get_spec_string(self):
        return self.specs


class RoundRobinArchive:

    def __init__(self, cf, xff, steps, rows):
        if cf not in ('LAST', 'MIN', 'MAX', 'AVERAGE'):
            raise ValueError('cf can only be LAST, MIN, MAX, AVERAGE')
        try:
            float(xff)
        except TypeError as te:
            raise te
        if not 0 <= float(xff) <= 1:
            raise ValueError('xff must be between 0 and 1')
        if not int(steps) > 0:
            raise ValueError('steps has to be positive')
        if not int(rows) > 0:
            raise ValueError('rows has to be positive')

        self.spec = str(cf) + ':' + str(xff) + ':' + str(steps) + ':' + str(rows)

    def get_complete_string(self):
        return 'RRA:' + self.spec

    def get_spec_string(self):
        return self.spec


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
        if not file.endswith('.rrd'):
            file += '.rrd'

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
            try:
                result = rrd.fetch(self.db, cf, time_parameters)
                ret[cf] = self._parse_result(result)
            except OperationalError:
                # If database doesn't contain round robin archive with given consolidate function, continue with next
                continue

        return ret

    def add_data_source(self, ds):
        rrd.tune(self.db, 'DS:' + ds.get_spec_string())

    def remove_data_source(self, ds):
        rrd.tune(self.db, 'DEL:' + ds.get_name())

    def add_rrd_archive(self, rra):
        rrd.tune(self.db, 'RRA:' + rra.get_spec_string())

    def remove_rrd_archive(self, idx):
        rrd.tune(self.db, 'DELRRA:' + str(idx))

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
