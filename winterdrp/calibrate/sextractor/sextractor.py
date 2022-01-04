import os
import logging
from winterdrp.paths import astrometry_output_dir
from winterdrp.calibrate.sourceextractor import run_sextractor, default_config
from winterdrp.preprocessing.base_processor import BaseProcessor
from winterdrp.preprocessing.image_saver import ImageSaver, latest_save_key

logger = logging.getLogger(__name__)


class SextractorRunner(BaseProcessor):

    base_key = "sextractor"

    requires = ["save"]

    def __init__(
            self,
            instrument_vars: dict,
            config: str = default_config,
            iteration: int = None,
            *args,
            **kwargs
    ):
        super().__init__(instrument_vars, *args, **kwargs)
        self.config = config
        self.iteration = iteration

    def _apply_to_images(
            self,
            images: list,
            headers: list,
            sub_dir: str = ""
    ) -> (list, list):

        # Try making output directory, unless it exists

        output_dir = astrometry_output_dir(sub_dir)

        try:
            os.makedirs(output_dir)
        except OSError:
            pass

        for header in list(headers):

            # First run Sextractor

            run_sextractor(
                header[latest_save_key],
                config=self.config,
                output_dir=output_dir,
            )

        return images, headers

    def check_prerequisites(
            self,
            preceding_steps: list,
    ):
        if preceding_steps[-1] != ImageSaver.base_key:
            err = f"Processor '{self.base_key}' must be preceded by {ImageSaver.base_key}. " \
                  f"However, the following preceding steps are found: {preceding_steps}."
            logger.error(err)
            raise ValueError(err)
