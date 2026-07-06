import config

# ============================================================
# アプリ全体のグローバル状態
# ============================================================

class AppState:
    def __init__(self):
        self.mode         = "video_select"
        self.video_path   = None
        self.current_slot = 0
        self.roi_config   = {
            "cost":  None,
            "slots": []
        }

state = AppState()


# ============================================================
# スロット状態管理
# ============================================================

class SlotState:
    def __init__(self):
        self.confirmed_card    = None
        self.candidate_card    = None
        self.candidate_count   = 0
        self.last_record_frame = -9999

    def update(self, detected_card):
        if detected_card is not None and detected_card is self.candidate_card:
            self.candidate_count += 1
        else:
            self.candidate_card  = detected_card
            self.candidate_count = 1 if detected_card is not None else 0
        new_confirmed = (
            self.candidate_card
            if self.candidate_count >= config.CARD_CONFIRM_NEED
            else None
        )

        prev = self.confirmed_card
        if prev is not None and new_confirmed is None:
            self.confirmed_card = None
            return "used", prev
        if new_confirmed is not None and new_confirmed is not prev:
            self.confirmed_card = new_confirmed
            return "new", new_confirmed

        return None, None

slot_states = {i: SlotState() for i in range(config.SLOT_COUNT)}


# ============================================================
# スキルカード定義・レジストリ
# ============================================================

class SkillCardDefinition:
    def __init__(self, character, image_path):
        self.character     = character
        self.original_path = image_path
        self.template      = None


class SkillCardRegistry:
    def __init__(self):
        self.cards = []

    def register(self, card_def):
        self.cards.append(card_def)

    def all_cards(self):
        return self.cards

card_registry = SkillCardRegistry()