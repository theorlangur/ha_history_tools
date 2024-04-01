from homeassistant.components.recorder import get_instance, history
from homeassistant.core import State
import homeassistant.util.dt as dt_util

DOMAIN = "history_tools"

ENTITY_ID_NAME = "entity_id"
START_TIME_ID = "start_time"
END_TIME_ID = "end_time"
MAX_CLIP_VALUE = "max_clip_value"
MIN_CLIP_VALUE = "min_clip_value"


def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    def _state_changes_during_period(
            entity_name, start_time, end_time
    ) -> list[State]:
        """Return state changes during a period."""
        return history.state_changes_during_period(
            hass,
            start_time,
            end_time,
            entity_name,
            include_start_time_state=True,
            no_attributes=True,
        ).get(entity_name, [])

    async def handle_integrate(call):
        """Handle the service call."""
        entity_name = call.data.get(ENTITY_ID_NAME)
        start_time = dt_util.as_utc(dt_util.parse_datetime(call.data.get(START_TIME_ID)) or dt_util.now())
        end_time = dt_util.as_utc(dt_util.parse_datetime(call.data.get(END_TIME_ID)) or dt_util.now())

        try:
            max_clip_value = float(call.data.get(MAX_CLIP_VALUE) or "")
        except ValueError:
            max_clip_value = None

        try:
            min_clip_value = float(call.data.get(MIN_CLIP_VALUE) or "")
        except ValueError:
            min_clip_value = None

        instance = get_instance(hass)
        states = await instance.async_add_executor_job( _state_changes_during_period,
                        entity_name,
                        start_time,
                        end_time
        )

        result = 0.0
        prev_val = None
        prev_t = None
        for s in states:
            val = float(s.state)
            if max_clip_value is not None and val > max_clip_value:
                val = max_clip_value
            if min_clip_value is not None and val < min_clip_value:
                val = min_clip_value
            t1 = s.last_changed.timestamp()
            if prev_val is not None and prev_t is not None:
                result = result + ((val + prev_val) / 2) * ((t1 - prev_t) / 3600)
            prev_val = val
            prev_t = t1

        hass.states.async_set(DOMAIN + ".integrate", result)

    hass.services.async_register(DOMAIN, "integrate", handle_integrate)

    # Return boolean to indicate that initialization was successful.
    return True

