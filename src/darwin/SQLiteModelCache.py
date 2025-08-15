import os
from pathlib import Path
from ast import literal_eval

import sqlite3
import threading

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from .ModelCache import ModelCache, register_model_cache
from .ModelRun import ModelRun
from .DarwinError import DarwinError

ALL_MODELS_FILE = "models.db"

lock = threading.Lock()


class SQLiteModelCache(ModelCache):
    def __init__(self):
        default_models_file = os.path.join(options.working_dir, ALL_MODELS_FILE)

        self.file = default_models_file

        utils.remove_file(default_models_file)

        if options.use_saved_models and options.saved_models_file:
            self.file = options.saved_models_file

        self.file = Path(self.file)

        if options.saved_models_readonly:
            log.message("Not saving any models.")
            return

        log.message(f"Models will be saved in {self.file}")

        if not self.file.is_file():
            create_database(self.file)

        self.conn = sqlite3.connect(self.file, check_same_thread=False)

        self.warmed_up = {}

        self.session = self.start_session()

    def start_session(self) -> int:
        with lock:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO session DEFAULT VALUES')

            self.conn.commit()

            cursor.execute(f"SELECT * FROM session ORDER BY id DESC LIMIT 1")

            cols = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        row = dict(zip(cols, rows[0]))

        return row['id']

    def store_model_run(self, run: ModelRun):
        """
        Store a run.
        """

        m = run.model
        r = run.result

        run.source = 'saved'

        values = (
            int("".join(str(b) for b in m.model_code.FullBinCode), 2),
            m.phenotype,
            run.generation,
            run.model_num,
            run.status,
            str(m.model_code.FullBinCode),
            str(m.model_code.IntCode),
            str(m.model_code.MinBinCode),
            m.non_influential_token_num,
            m.omega_num,
            m.sigma_num,
            m.theta_num,
            r.estimated_omega_num,
            r.estimated_sigma_num,
            r.estimated_theta_num,
            int(r.success),
            int(r.correlation),
            int(r.covariance),
            r.ofv,
            r.condition_num,
            r.fitness,
            str(r.f) if options.isMOGA3 else None,
            str(r.g) if options.isMOGA3 else None,
            r.post_run_python_penalty if not options.isMOGA3 else None,
            r.post_run_python_text if not options.isMOGA3 else None,
            r.post_run_r_penalty if not options.isMOGA3 else None,
            r.post_run_r_text if not options.isMOGA3 else None,
            r.errors,
            r.messages,
            run.file_stem,
            run.run_dir,
            run.control_file_name,
            run.output_file_name,
            run.executable_file_name,
            m.control,
            run.source,
            self.session
        )

        questions = ', '.join(['?'] * len(values))

        with lock:
            cursor = self.conn.cursor()

            cursor.execute(f"""
                INSERT INTO model_runs (
                    id, phenotype,
                    generation, model_num, status,
                    FullBinCode, IntCode, MinBinCode,
                    non_influential_token_num,
                    omega_num, sigma_num, theta_num,
                    estimated_omega_num, estimated_sigma_num, estimated_theta_num,
                    success, correlation, covariance,
                    ofv, condition_num, fitness,
                    f, g,
                    post_run_python_penalty, post_run_python_text,
                    post_run_r_penalty, post_run_r_text,
                    errors, messages,
                    file_stem, run_dir, control_file_name, output_file_name, executable_file_name,
                    control, source, session_id
                )
                VALUES ({questions})
            """, values)

            self.conn.commit()

    def warm_up(self, run: ModelRun):
        crun = self.find_model_run(model_code=run.model.model_code) \
            or self.find_model_run(model_code=run.model.phenotype)

        if crun is not None:
            self.warmed_up[run.model.phenotype] = (run.run_dir, run.model.control)

    def find_model_run(self, **kwargs) -> ModelRun or None:
        if 'model_code' in kwargs:
            model = kwargs['model_code']
            value = int("".join(str(b) for b in model.FullBinCode), 2)
            cond = f"id = ?"
        elif 'phenotype' in kwargs:
            value = kwargs['phenotype']
            cond = f"phenotype = ? LIMIT 1"
        else:
            raise DarwinError('Expected model_code or phenotype')

        with lock:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM model_runs WHERE {cond}", (value,))
            cols = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        if not rows:
            return None

        row = dict(zip(cols, rows[0]))

        model_code = dict((col, literal_eval(row[col])) for col in ('FullBinCode', 'MinBinCode', 'IntCode'))
        model = dict((col, row[col]) for col in ('phenotype', 'control', 'non_influential_token_num',
                                                 'omega_num', 'sigma_num', 'theta_num'))
        result = dict((col, row[col])
                      for col in ('success', 'correlation', 'covariance', 'condition_num', 'ofv', 'fitness', 'f', 'g',
                                  'post_run_python_penalty', 'post_run_python_text',
                                  'post_run_r_penalty', 'post_run_r_text',
                                  'estimated_omega_num', 'estimated_sigma_num', 'estimated_theta_num',
                                  'errors', 'messages'))

        if options.isMOGA3:
            result['f'] = literal_eval(result['f'])
            result['g'] = literal_eval(result['g'])

        result['success'] = bool(result['success'])
        result['correlation'] = bool(result['correlation'])
        result['covariance'] = bool(result['covariance'])

        model['model_code'] = model_code

        run_dict = dict((col, row[col])
                        for col in ('model_num', 'generation', 'file_stem', 'run_dir', 'control_file_name',
                                    'output_file_name', 'executable_file_name', 'source', 'status'))

        run_dict['model'] = model
        run_dict['result'] = result

        run = ModelRun.from_dict(run_dict)

        wr = self.warmed_up.get(run.model.phenotype, None)

        if wr is not None:
            (run.run_dir, run.model.control) = wr
        elif row['session_id'] == self.session:
            # added in this session
            pass
        else:
            run.status = 'Restored'
            run.cold = True

        return run

    def finalize(self):
        """
        Finalize all ongoing activities.
        """

        self.conn.close()


def create_database(db_name: Path):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_runs (
        id INTEGER PRIMARY KEY,
        phenotype TEXT,
        generation TEXT,
        model_num INTEGER,
        status TEXT,
        FullBinCode TEXT,
        IntCode TEXT,
        MinBinCode TEXT,
        non_influential_token_num INTEGER,
        omega_num INTEGER,
        sigma_num INTEGER,
        theta_num INTEGER,
        estimated_omega_num INTEGER,
        estimated_sigma_num INTEGER,
        estimated_theta_num INTEGER,
        success INTEGER,
        correlation INTEGER,
        covariance INTEGER,
        ofv REAL,
        condition_num REAL,
        fitness REAL,
        f TEXT,
        g TEXT,
        post_run_python_penalty REAL,
        post_run_python_text TEXT,
        post_run_r_penalty REAL,
        post_run_r_text TEXT,
        errors TEXT,
        messages TEXT,
        file_stem TEXT,
        run_dir TEXT,
        control_file_name TEXT,
        output_file_name TEXT,
        executable_file_name TEXT,
        control TEXT,
        source TEXT,
        session_id INTEGER
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phenotype ON model_runs(phenotype)")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def register():
    """
    :data:`Register <darwin.ModelCache.register_model_cache>`
    :data:`SQLiteModelCache <darwin.SQLiteModelCache.SQLiteModelCache>`
    """
    register_model_cache('darwin.SQLiteModelCache', SQLiteModelCache)
