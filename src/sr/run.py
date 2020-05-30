# Copyright 2020 QuantumBlack Visual Analytics Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# NONINFRINGEMENT. IN NO EVENT WILL THE LICENSOR OR OTHER CONTRIBUTORS
# BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF, OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The QuantumBlack Visual Analytics Limited ("QuantumBlack") name and logo
# (either separately or in combination, "QuantumBlack Trademarks") are
# trademarks of QuantumBlack. The License does not grant you any right or
# license to the QuantumBlack Trademarks. You may not use the QuantumBlack
# Trademarks or any confusingly similar mark as a trademark for your product,
# or use the QuantumBlack Trademarks in any other manner that might cause
# confusion in the marketplace, including but not limited to in advertising,
# on websites, or on software.
#
# See the License for the specific language governing permissions and
# limitations under the License.

"""Application entry point."""
import os
from pathlib import Path
from typing import Dict, Any, Callable

from kedro.io import DataCatalog, AbstractDataSet

from sr.pipeline import create_pipelines
from kedro.framework.context import KedroContext, load_package_context
from kedro.pipeline import Pipeline


class ProjectContext(KedroContext):
    """Users can override the remaining methods from the parent class here,
    or create new ones (e.g. as required by plugins)
    """

    project_name = "semi-realtime"
    # `project_version` is the version of kedro used to generate the project
    project_version = "0.16.1"
    package_name = "sr"

    _twitter_dataset_name = "raw_tweets"
    _twitter_keywords = ["kedro", "python"]

    def _get_pipelines(self) -> Dict[str, Pipeline]:
        return create_pipelines()

    def _init_twitter_stream(self):
        import tweepy
        import logging

        creds = self.config_loader.get("credentials*")
        screen_names_to_ignore = set(
            self.config_loader.get("parameters*")["screen_names_to_ignore"]
        )
        auth = tweepy.OAuthHandler(creds["consumer_key"], creds["consumer_secret"])
        auth.set_access_token(creds["access_token"], creds["access_token_secret"])

        api = tweepy.API(auth)

        logger = logging.getLogger("TweetToYaml")

        class TweetToYamlListener(tweepy.StreamListener):
            def __init__(self, save_tweet: Callable, *args, **kwargs):
                self._save_tweet = save_tweet
                super().__init__(*args, **kwargs)

            def on_status(self, status):
                if status.user.screen_name in screen_names_to_ignore:
                    logger.info(f"Ignoring tweet {status.user.screen_name}")
                    return
                import datetime

                dstr = "%Y-%m-%dT%H:%M:%S:%f"
                current_dt = datetime.datetime.now().strftime(dstr)
                self._save_tweet({current_dt: status._json})
                printable_text = status.text.split("\n")[0]
                logger.info(f"Saved Tweet {status.user.screen_name}: {printable_text}")

        self._listener = TweetToYamlListener(
            lambda x: self.catalog.save(self._twitter_dataset_name, x)
        )
        self._stream = tweepy.Stream(api.auth, listener=self._listener)
        self._stream.filter(track=self._twitter_keywords, is_async=True)

    def run(  # pylint: disable=too-many-arguments,too-many-locals
        self, *args, **kwargs
    ) -> Dict[str, Any]:
        self._init_twitter_stream()
        return super().run(*args, **kwargs)


def run_package():
    # Entry point for running a Kedro project packaged with `kedro package`
    # using `python -m <project_package>.run` command.
    project_context = load_package_context(
        project_path=Path.cwd(), package_name=Path(__file__).resolve().parent.name
    )
    project_context.run()


if __name__ == "__main__":
    run_package()
