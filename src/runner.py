import time
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.runner import SequentialRunner


class StreamingRunner(SequentialRunner):
    def _run(
        self, pipeline: Pipeline, catalog: DataCatalog, run_id: str = None
    ) -> None:
        while True:
            super()._run(pipeline, catalog, run_id)
            time.sleep(10)
