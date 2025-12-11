from aiogram.fsm.state import State, StatesGroup

class Order(StatesGroup):
    """
    States for the ordering process.
    """
    choosing_location = State()
    choosing_product = State()
    choosing_volume = State()
    choosing_milk = State()
    choosing_syrup = State()
    choosing_quantity = State()
    entering_pickup_time = State()
    choosing_payment_method = State()
    confirming_order = State()

class Broadcast(StatesGroup):
    """
    States for the broadcast process.
    """
    waiting_for_message = State()
    confirming_broadcast = State()
