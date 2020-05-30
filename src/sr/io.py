from copy import deepcopy
from typing import List, Dict, Callable, Any

from kedro.io import IncrementalDataSet, PartitionedDataSet


class UncachedIncrementalDataSet(IncrementalDataSet):
    def _list_partitions(self) -> List[str]:
        checkpoint = self._read_checkpoint()
        checkpoint_path = self._filesystem._strip_protocol(  # pylint: disable=protected-access
            self._checkpoint_config[self._filepath_arg]
        )

        def _is_valid_partition(partition) -> bool:
            if not partition.endswith(self._filename_suffix):
                return False
            if partition == checkpoint_path:
                return False
            if checkpoint is None:
                # nothing was processed yet
                return True
            partition_id = self._path_to_partition(partition)
            return self._comparison_func(partition_id, checkpoint)

        return sorted(
            part
            for part in self._filesystem.find(self._normalized_path, **self._load_args)
            if _is_valid_partition(part)
        )


class UncachedPartitionedDataSet(PartitionedDataSet):
    def _list_partitions(self) -> List[str]:
        return [
            path
            for path in self._filesystem.find(self._normalized_path, **self._load_args)
            if path.endswith(self._filename_suffix)
        ]

    def _load(self) -> Dict[str, Callable[[], Any]]:
        partitions = {}

        for partition in self._list_partitions():
            kwargs = deepcopy(self._dataset_config)
            # join the protocol back since PySpark may rely on it
            kwargs[self._filepath_arg] = self._join_protocol(partition)
            dataset = self._dataset_type(**kwargs)  # type: ignore
            partition_id = self._path_to_partition(partition)
            partitions[partition_id] = dataset.load

        return partitions
