"""Scene scheduler module."""
import asyncio
import logging
import time
from typing import Dict, List, Optional

from .controller import WLEDController
from .gui import MusicPlayer
from .models import TimedEvent

LOGGER = logging.getLogger(__name__)

class SceneScheduler:
    """Schedules events and dispatches controller scenes."""
    def __init__(self, controllers: Dict[str, List[WLEDController]], dry_run: bool = False):
        self.controllers = controllers
        self.dry_run = dry_run

    async def run_schedule(self, events: List[TimedEvent], music_player: Optional[MusicPlayer] = None) -> None:
        if not events:
            LOGGER.warning("No events to schedule.")
            return

        events.sort()
        reference = time.perf_counter() - (music_player.playback_elapsed() or 0)
        for event in events:
            sleep_for = reference + event.time_s - time.perf_counter()
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
            await self._dispatch_event(event)

    async def _dispatch_event(self, event: TimedEvent) -> None:
        dispatch_start = time.perf_counter()
        LOGGER.info("Dispatching event @%.2fs", event.time_s)
        
        # Prepare all requests in parallel
        tasks = []
        try:
            for cscene in event.controller_scenes:
                controllers = self.controllers.get(cscene.controller_id, [])
                if not controllers:
                    LOGGER.warning("Controller %s not defined", cscene.controller_id)
                    continue
                    
                # Create tasks for all instances of this controller
                for ctrl in controllers:
                    task = asyncio.create_task(
                        ctrl.apply_scene(cscene.scene, dry_run=self.dry_run)
                    )
                    tasks.append((f"{cscene.controller_id}_{ctrl.base_url}", task))
            
            # Wait for all tasks with a timeout
            if tasks:
                # Use wait instead of gather to handle timeouts better
                done, pending = await asyncio.wait(
                    [t for _, t in tasks],
                    timeout=0.5  # Use same timeout as WLEDController.WLED_HTTP_TIMEOUT
                )
                
                try:
                    # Cancel any pending tasks that didn't complete in time
                    for pending_task in pending:
                        pending_task.cancel()
                        try:
                            await pending_task
                        except asyncio.CancelledError:
                            pass
                    
                    # Log results
                    total_time = time.perf_counter() - dispatch_start
                    success_count = len(done)
                    timeout_count = len(pending)
                    
                    if timeout_count:
                        LOGGER.warning(
                            "Event @%.2fs: %d/%d controllers responded (%.3fs), %d timed out",
                            event.time_s, success_count, len(tasks), total_time, timeout_count
                        )
                    else:
                        LOGGER.debug(
                            "Event @%.2fs: All %d controllers responded in %.3fs",
                            event.time_s, len(tasks), total_time
                        )
                except Exception as e:
                    LOGGER.error("Error while cleaning up tasks: %s", e)
        except Exception as e:
            LOGGER.error("Error dispatching event @%.2fs: %s", event.time_s, e)
            # Ensure any created tasks are cleaned up
            for _, task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    async def close(self) -> None:
        """Close all controller sessions properly."""
        close_tasks = []
        for controller_list in self.controllers.values():
            for controller in controller_list:
                if controller._internal_session:
                    close_tasks.append(controller.close())
        
        if close_tasks:
            # Wait for all sessions to close
            await asyncio.gather(*close_tasks)
