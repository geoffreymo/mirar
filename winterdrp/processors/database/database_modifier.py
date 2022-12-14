import logging
from abc import ABC
from collections.abc import Callable
from typing import Optional

import astropy.io.fits
import numpy as np
import pandas as pd
from astropy.io.fits import Header

from winterdrp.data import ImageBatch, SourceBatch
from winterdrp.processors.base_processor import (
    BaseDataframeProcessor,
    BaseImageProcessor,
)
from winterdrp.processors.database.base_database_processor import (
    BaseDatabaseProcessor,
    DataBaseError,
)
from winterdrp.processors.database.database_importer import (
    BaseDatabaseImporter,
    BaseImageDatabaseImporter,
)
from winterdrp.processors.database.postgres import (
    get_sequence_keys_from_table,
    modify_db_entry,
)

logger = logging.getLogger(__name__)


class BaseDatabaseModifier(BaseDatabaseImporter, ABC):
    base_key = "dbmodifier"

    def __init__(self, db_alter_columns: Optional[str] = None, *args, **kwargs):
        super(BaseDatabaseModifier, self).__init__(
            db_output_columns=db_alter_columns, *args, **kwargs
        )
        self.db_alter_columns = db_alter_columns


class ImageDatabaseModifier(BaseDatabaseModifier, BaseImageDatabaseImporter):
    def __init__(self, *args, **kwargs):
        super(ImageDatabaseModifier, self).__init__(*args, **kwargs)

    def _apply_to_images(
        self,
        batch: ImageBatch,
    ) -> ImageBatch:
        for image in batch:
            query_columns, accepted_values, accepted_types = self.get_constraints(image)
            logger.info(f"{query_columns}, {accepted_values}, {accepted_types}")

            modify_db_entry(
                value_dict=image,
                db_query_columns=query_columns,
                db_query_values=accepted_values,
                db_query_comparison_types=accepted_types,
                db_alter_columns=self.db_alter_columns,
                db_table=self.db_table,
                db_name=self.db_name,
                db_user=self.db_user,
                password=self.db_password,
            )

        return batch


class ModifyImageDatabaseSeq(ImageDatabaseModifier):
    def __init__(self, sequence_key: Optional[str | list[str]] = None, *args, **kwargs):
        super(ModifyImageDatabaseSeq, self).__init__(*args, **kwargs)
        self.sequence_key = sequence_key

    def get_constraints(self, image):
        if self.sequence_key is None:
            self.sequence_key = [
                x
                for x in get_sequence_keys_from_table(
                    self.db_table, self.db_name, self.db_user, self.db_password
                )
            ]

        accepted_values = [image[x.upper()] for x in self.sequence_key]
        accepted_types = ["="] * len(accepted_values)
        return self.sequence_key, accepted_values, accepted_types


class DataframeDatabaseModifier(BaseDatabaseModifier, BaseDataframeProcessor):
    def __init__(self, *args, **kwargs):
        super(DataframeDatabaseModifier, self).__init__(*args, **kwargs)

    def _apply_to_candidates(
        self,
        batch: SourceBatch,
    ) -> SourceBatch:
        return SourceBatch
