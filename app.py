import streamlit as st
import time

# ─────────────────────────────────────────────────────────────────
#  DFA CORE IMPLEMENTATION
# ─────────────────────────────────────────────────────────────────

# All DFA states
STATES = {
    "q0": "Card Inserted / Idle",
    "q1": "PIN Entry",
    "q2": "Authenticated",
    "q3": "Transaction Menu",
    "q4": "Withdraw",
    "q5": "Balance Inquiry",
    "q6": "Session Complete",
    "qD": "DEAD STATE (Error)",
}

# Start state, final states, dead state
START_STATE   = "q0"
FINAL_STATES  = {"q6"}
DEAD_STATE    = "qD"

# DFA Transition Function  δ(state, input) → next_state
# Inputs: insert_card, enter_pin, pin_correct, pin_wrong,
#         select_withdraw, select_balance, confirm_withdraw,
#         cancel, exit
TRANSITION_TABLE = {
    "q0": {
        "insert_card":      "q1",
        "enter_pin":        "qD",   # Can't enter PIN without card
        "pin_correct":      "qD",
        "pin_wrong":        "qD",
        "select_withdraw":  "qD",
        "select_balance":   "qD",
        "confirm_withdraw": "qD",
        "cancel":           "q0",
        "exit":             "q0",
    },
    "q1": {
        "insert_card":      "qD",   # Card already inserted
        "enter_pin":        "q1",   # Stay until validated
        "pin_correct":      "q2",   # Correct PIN → Authenticated
        "pin_wrong":        "q1",   # Wrong PIN → retry (handled separately)
        "select_withdraw":  "qD",
        "select_balance":   "qD",
        "confirm_withdraw": "qD",
        "cancel":           "q0",   # Cancel → eject card
        "exit":             "q0",
    },
    "q2": {
        "insert_card":      "qD",
        "enter_pin":        "qD",
        "pin_correct":      "qD",
        "pin_wrong":        "qD",
        "select_withdraw":  "q4",   # Go to Withdraw state
        "select_balance":   "q5",   # Go to Balance state
        "confirm_withdraw": "qD",
        "cancel":           "q3",
        "exit":             "q6",   # Exit → session complete
    },
    "q3": {
        "insert_card":      "qD",
        "enter_pin":        "qD",
        "pin_correct":      "qD",
        "pin_wrong":        "qD",
        "select_withdraw":  "q4",
        "select_balance":   "q5",
        "confirm_withdraw": "qD",
        "cancel":           "q3",
        "exit":             "q6",
    },
    "q4": {
        "insert_card":      "qD",
        "enter_pin":        "qD",
        "pin_correct":      "qD",
        "pin_wrong":        "qD",
        "select_withdraw":  "qD",
        "select_balance":   "qD",
        "confirm_withdraw": "q3",   # After withdraw → back to menu
        "cancel":           "q3",   # Cancel → back to menu
        "exit":             "q6",
    },
    "q5": {
        "insert_card":      "qD",
        "enter_pin":        "qD",
        "pin_correct":      "qD",
        "pin_wrong":        "qD",
        "select_withdraw":  "qD",
        "select_balance":   "qD",
        "confirm_withdraw": "qD",
        "cancel":           "q3",   # Back to menu
        "exit":             "q6",
    },
    "q6": {
        "insert_card":      "q1",   # New session
        "enter_pin":        "qD",
        "pin_correct":      "qD",
        "pin_wrong":        "qD",
        "select_withdraw":  "qD",
        "select_balance":   "qD",
        "confirm_withdraw": "qD",
        "cancel":           "q6",
        "exit":             "q6",
    },
    "qD": {
        # Dead state – absorbing; all inputs stay in qD
        k: "qD" for k in [
            "insert_card","enter_pin","pin_correct","pin_wrong",
            "select_withdraw","select_balance","confirm_withdraw",
            "cancel","exit"
        ]
    },
}

CORRECT_PIN = "1234"     # Demo PIN
MAX_PIN_ATTEMPTS = 3     # Lock after 3 wrong attempts


def dfa_transition(current_state: str, symbol: str) -> str:
    """
    δ(current_state, symbol) → next_state
    Returns the next state given a state and input symbol.
    """
    return TRANSITION_TABLE.get(current_state, {}).get(symbol, DEAD_STATE)


# ─────────────────────────────────────────────────────────────────
#  SESSION STATE INITIALISATION
# ─────────────────────────────────────────────────────────────────

def init_session():
    """Initialise all Streamlit session variables on first load."""
    defaults = {
        "dfa_state":       START_STATE,
        "balance":         5000000,        # PKR
        "pin_attempts":    0,
        "history":         [],           # list of (state_before, symbol, state_after)
        "message":         "Welcome! Please insert your card to begin.",
        "message_type":    "info",       # info | success | error | warning
        "withdraw_amount": 0,
        "locked":          False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def log_transition(before: str, symbol: str, after: str):
    """Append a transition to the history log."""
    st.session_state.history.append({
        "from":   before,
        "symbol": symbol,
        "to":     after,
        "label_from": STATES.get(before, before),
        "label_to":   STATES.get(after, after),
    })


def apply_input(symbol: str):
    """Apply a DFA input symbol and update session state."""
    before = st.session_state.dfa_state
    after  = dfa_transition(before, symbol)
    log_transition(before, symbol, after)
    st.session_state.dfa_state = after
    return before, after


# ─────────────────────────────────────────────────────────────────
#  STREAMLIT PAGE CONFIG & GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ATM DFA Simulator",
    page_icon="🏧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background: #0d0f14;
    color: #e8eaf0;
}

/* ── ATM card panel ── */
.atm-panel {
    background: linear-gradient(135deg, #1a1d2e 0%, #0f1118 100%);
    border: 1px solid #2a2d3e;
    border-radius: 16px;
    padding: 28px 32px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
}

/* ── State badge ── */
.state-badge {
    display: inline-block;
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: #fff;
    font-family: 'Space Mono', monospace;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 999px;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
.state-dead {
    background: linear-gradient(90deg, #ff416c, #ff4b2b);
}
.state-final {
    background: linear-gradient(90deg, #11998e, #38ef7d);
}

/* ── ATM screen ── */
.atm-screen {
    background: #0a0e1a;
    border: 1px solid #1e2235;
    border-radius: 10px;
    padding: 18px 22px;
    font-family: 'Space Mono', monospace;
    font-size: 0.9rem;
    min-height: 80px;
    color: #7effc4;
    line-height: 1.7;
}

/* ── Section titles ── */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #555a7a;
    margin-bottom: 10px;
}

/* ── Transition row ── */
.tr-row {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #12151f;
    border-left: 3px solid #0072ff;
    border-radius: 6px;
    padding: 7px 12px;
    margin-bottom: 6px;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    color: #9fa3b8;
}
.tr-row.dead { border-left-color: #ff4b2b; }
.tr-row.final { border-left-color: #38ef7d; }
.tr-arrow { color: #0072ff; margin: 0 4px; }

/* ── Streamlit button overrides ── */
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(0,114,255,0.3) !important;
}

/* ── Table ── */
.dfa-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
}
.dfa-table th {
    background: #1a1d2e;
    color: #0072ff;
    padding: 8px 10px;
    text-align: center;
    border: 1px solid #2a2d3e;
}
.dfa-table td {
    padding: 6px 10px;
    border: 1px solid #1e2235;
    text-align: center;
    color: #9fa3b8;
}
.dfa-table tr:nth-child(even) td { background: #0f1118; }
.dead-cell { color: #ff4b2b !important; font-weight: bold; }
.final-cell { color: #38ef7d !important; font-weight: bold; }
.current-state-row td { background: #0d1a30 !important; color: #00c6ff !important; font-weight: bold; }

/* ── Divider ── */
hr.atm-divider {
    border: none;
    border-top: 1px solid #1e2235;
    margin: 18px 0;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────────

init_session()

# ─── HEADER ───────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 20px 0 10px 0;">
  <div style="font-family:'Syne',sans-serif; font-size:2.6rem; font-weight:800;
              background:linear-gradient(90deg,#00c6ff,#0072ff,#00c6ff);
              -webkit-background-clip:text; -webkit-text-fill-color:transparent;
              background-clip:text;">
    🏧 ATM DFA Simulator
  </div>
  <div style="color:#555a7a; font-size:0.9rem; margin-top:4px; font-family:'Space Mono',monospace;">
    Theory of Automata &nbsp;|&nbsp; Deterministic Finite Automata
  </div>
</div>
""", unsafe_allow_html=True)

# ─── LAYOUT: LEFT panel + RIGHT panel ────────────────────────────
left_col, right_col = st.columns([1, 1], gap="large")

# ═══════════════════════════════════════════════════════════════
# LEFT COLUMN – ATM Interface
# ═══════════════════════════════════════════════════════════════
with left_col:

    cur_state = st.session_state.dfa_state
    locked    = st.session_state.locked

    # ── Current DFA State ──────────────────────────────────────
    badge_cls = "state-badge"
    if cur_state == DEAD_STATE:
        badge_cls += " state-dead"
    elif cur_state in FINAL_STATES:
        badge_cls += " state-final"

    st.markdown(f"""
    <div class="atm-panel">
      <div class="section-title">Current DFA State</div>
      <span class="{badge_cls}">{cur_state}</span>
      <div style="font-size:1.1rem; font-weight:600; margin-top:6px;">
        {STATES.get(cur_state, cur_state)}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── ATM Screen ─────────────────────────────────────────────
    msg = st.session_state.message
    st.markdown(f"""
    <div class="atm-panel">
      <div class="section-title">ATM Screen</div>
      <div class="atm-screen">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────
    #  STATE-SPECIFIC UI PANELS
    # ──────────────────────────────────────────────────────────

    # ── q0: Idle – Insert Card ─────────────────────────────────
    if cur_state == "q0":
        with st.container():
            st.markdown('<div class="section-title">Action Required</div>', unsafe_allow_html=True)
            if st.button("💳  Insert Card", use_container_width=True, type="primary"):
                before, after = apply_input("insert_card")
                st.session_state.pin_attempts = 0
                st.session_state.locked = False
                st.session_state.message = (
                    "Card detected.\n\n"
                    "Please enter your 4-digit PIN to authenticate."
                )
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ── q1: PIN Entry ──────────────────────────────────────────
    elif cur_state == "q1":
        with st.container():
            st.markdown('<div class="section-title">PIN Authentication</div>', unsafe_allow_html=True)

            attempts_left = MAX_PIN_ATTEMPTS - st.session_state.pin_attempts
            st.info(f"Attempts remaining: **{attempts_left}**")

            pin_input = st.text_input(
                "Enter 4-digit PIN",
                max_chars=4,
                type="password",
                placeholder="● ● ● ●",
                key="pin_field"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔐  Login", use_container_width=True, type="primary"):
                    if pin_input == CORRECT_PIN:
                        apply_input("pin_correct")
                        st.session_state.message = (
                            "✅  Authentication Successful!\n\n"
                            "Welcome! Please select a transaction."
                        )
                    else:
                        st.session_state.pin_attempts += 1
                        apply_input("pin_wrong")
                        remaining = MAX_PIN_ATTEMPTS - st.session_state.pin_attempts
                        if remaining <= 0:
                            # Lock the card → go dead
                            apply_input("pin_wrong")   # Force dead on 3rd fail
                            st.session_state.locked = True
                            st.session_state.dfa_state = DEAD_STATE
                            st.session_state.message = (
                                "🚫  Card BLOCKED!\n\n"
                                "Too many incorrect PIN attempts.\n"
                                "Please contact your bank."
                            )
                        else:
                            st.session_state.message = (
                                f"❌  Incorrect PIN.\n\n"
                                f"{remaining} attempt(s) remaining."
                            )
                    st.rerun()

            with col_b:
                if st.button("✖  Cancel", use_container_width=True):
                    apply_input("cancel")
                    st.session_state.message = "Session cancelled. Card ejected."
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── q2 / q3: Transaction Menu ─────────────────────────────
    elif cur_state in ("q2", "q3"):
        with st.container():
            st.markdown('<div class="section-title">Select Transaction</div>', unsafe_allow_html=True)

            st.success(f"💰  Account Balance: **PKR {st.session_state.balance:,}**")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💵  Withdraw Cash", use_container_width=True, type="primary"):
                    apply_input("select_withdraw")
                    st.session_state.message = "Withdraw Cash\n\nEnter the amount you wish to withdraw."
                    st.rerun()
            with c2:
                if st.button("📊  Balance Inquiry", use_container_width=True):
                    apply_input("select_balance")
                    st.session_state.message = (
                        f"Balance Inquiry\n\n"
                        f"Current Balance: PKR {st.session_state.balance:,}"
                    )
                    st.rerun()

            if st.button("🚪  Exit / Eject Card", use_container_width=True):
                apply_input("exit")
                st.session_state.message = "Thank you for using our ATM.\nCard ejected. Have a nice day!"
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── q4: Withdraw ──────────────────────────────────────────
    elif cur_state == "q4":
        with st.container():
            st.markdown('<div class="section-title">Cash Withdrawal</div>', unsafe_allow_html=True)

            st.info(f"Available Balance: **PKR {st.session_state.balance:,}**")

            # Quick amount buttons
            st.markdown("**Quick Amounts (PKR)**")
            qa_cols = st.columns(4)
            quick_amounts = [1000, 5000, 10000, 20000]
            for i, amt in enumerate(quick_amounts):
                with qa_cols[i]:
                    if st.button(f"{amt:,}", use_container_width=True):
                        st.session_state.withdraw_amount = amt

            amount = st.number_input(
                "Or enter custom amount (PKR)",
                min_value=0,
                max_value=st.session_state.balance,
                step=500,
                value=st.session_state.withdraw_amount,
                key="withdraw_field"
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅  Confirm Withdraw", use_container_width=True, type="primary"):
                    if amount <= 0:
                        st.error("Please enter a valid amount.")
                    elif amount > st.session_state.balance:
                        st.error("Insufficient balance!")
                    else:
                        st.session_state.balance -= amount
                        apply_input("confirm_withdraw")
                        st.session_state.message = (
                            f"✅  Withdrawal Successful!\n\n"
                            f"Amount Dispensed : PKR {amount:,}\n"
                            f"Remaining Balance: PKR {st.session_state.balance:,}"
                        )
                        st.session_state.withdraw_amount = 0
                        st.rerun()
            with c2:
                if st.button("✖  Cancel", use_container_width=True):
                    apply_input("cancel")
                    st.session_state.message = "Withdrawal cancelled."
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── q5: Balance Inquiry ───────────────────────────────────
    elif cur_state == "q5":
        with st.container():
            st.markdown('<div class="section-title">Balance Inquiry</div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div style="text-align:center; padding:24px 0;">
              <div style="font-size:0.8rem; color:#555a7a; font-family:'Space Mono',monospace;">
                AVAILABLE BALANCE
              </div>
              <div style="font-size:2.4rem; font-weight:800; color:#38ef7d; font-family:'Syne',sans-serif;">
                PKR {st.session_state.balance:,}
              </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("◀  Back to Menu", use_container_width=True, type="primary"):
                apply_input("cancel")
                st.session_state.message = "Returning to transaction menu."
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── q6: Session Complete ──────────────────────────────────
    elif cur_state == "q6":
        with st.container():
            st.markdown("""
            <div style="text-align:center; padding:20px 0;">
              <div style="font-size:3rem;">✅</div>
              <div style="font-size:1.4rem; font-weight:800; color:#38ef7d;">Session Complete</div>
              <div style="color:#9fa3b8; margin-top:8px;">Thank you for banking with us!</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔄  New Transaction", use_container_width=True, type="primary"):
                # Reset everything
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── qD: Dead / Error State ────────────────────────────────
    elif cur_state == DEAD_STATE:
        with st.container():
            st.markdown('<div class="atm-panel">', unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center; padding:20px 0;">
              <div style="font-size:3rem;">🚫</div>
              <div style="font-size:1.4rem; font-weight:800; color:#ff4b2b;">
                DEAD STATE — System Error
              </div>
              <div style="color:#9fa3b8; margin-top:8px;">
                An invalid operation occurred. Please restart.
              </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔄  Restart System", use_container_width=True, type="primary"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# RIGHT COLUMN – DFA Visualisation
# ═══════════════════════════════════════════════════════════════
with right_col:

    # ── Transition History ─────────────────────────────────────

    st.markdown('<div class="section-title">Live DFA Transition Log</div>', unsafe_allow_html=True)

    history = st.session_state.history
    if not history:
        st.markdown(
            '<div style="color:#555a7a; font-family:\'Space Mono\',monospace; font-size:0.8rem;">'
            'No transitions yet. Insert card to begin...</div>',
            unsafe_allow_html=True
        )
    else:
        # Show last 8 transitions (most recent on top)
        for t in reversed(history[-8:]):
            is_dead  = t["to"] == DEAD_STATE
            is_final = t["to"] in FINAL_STATES
            row_cls  = "tr-row dead" if is_dead else ("tr-row final" if is_final else "tr-row")
            st.markdown(f"""
            <div class="{row_cls}">
              <span style="color:#e8eaf0;font-weight:600">{t['from']}</span>
              <span style="color:#555a7a"> ({t['label_from'][:18]})</span>
              <span class="tr-arrow"> ──[{t['symbol']}]──▶ </span>
              <span style="color:#e8eaf0;font-weight:600">{t['to']}</span>
              <span style="color:#555a7a"> ({t['label_to'][:18]})</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── DFA State Diagram (ASCII / Text) ──────────────────────
    st.markdown('<div class="section-title">DFA State Diagram</div>', unsafe_allow_html=True)

    cur = st.session_state.dfa_state

    def state_html(sid, active):
        label = STATES.get(sid, sid)
        if sid == DEAD_STATE:
            color = "#ff4b2b"
        elif sid in FINAL_STATES:
            color = "#38ef7d"
        else:
            color = "#0072ff"

        if active:
            bg = f"background:linear-gradient(135deg,{color}33,{color}11); border:2px solid {color};"
        else:
            bg = "background:#12151f; border:1px solid #2a2d3e;"

        return f"""
        <div style="{bg} border-radius:10px; padding:6px 10px; margin:4px 0;
                    font-family:'Space Mono',monospace; font-size:0.72rem;">
          <span style="color:{color}; font-weight:700;">{sid}</span>
          <span style="color:#9fa3b8; margin-left:8px;">{label}</span>
          {'<span style="float:right; font-size:0.7rem; color:#38ef7d;">● ACTIVE</span>' if active else ''}
        </div>
        """

    for sid in STATES:
        st.markdown(state_html(sid, sid == cur), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Condensed Transition Table ────────────────────────────
    with st.expander("📋  Full Transition Table (δ)", expanded=False):
        symbols_short = ["insert", "pin✓", "pin✗", "withdraw", "balance", "confirm", "cancel", "exit"]
        symbols_full  = ["insert_card","pin_correct","pin_wrong",
                         "select_withdraw","select_balance","confirm_withdraw","cancel","exit"]

        header = "<tr><th>State</th>" + "".join(f"<th>{s}</th>" for s in symbols_short) + "</tr>"
        rows = ""
        for sid, sname in STATES.items():
            is_cur = sid == cur
            row_cls = 'class="current-state-row"' if is_cur else ""
            cells = f"<td>{sid}</td>"
            for sym in symbols_full:
                nxt = TRANSITION_TABLE.get(sid, {}).get(sym, DEAD_STATE)
                cell_cls = ""
                if nxt == DEAD_STATE:   cell_cls = ' class="dead-cell"'
                elif nxt in FINAL_STATES: cell_cls = ' class="final-cell"'
                cells += f"<td{cell_cls}>{nxt}</td>"
            rows += f"<tr {row_cls}>{cells}</tr>"

        st.markdown(
            f'<div style="overflow-x:auto"><table class="dfa-table">{header}{rows}</table></div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────────────────────────
# SIDEBAR – Theory Info
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:1.3rem; font-weight:800;
                color:#0072ff; margin-bottom:4px;">
      📖 Theory Reference
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### DFA Definition")
    st.markdown("""
    A **DFA** is a 5-tuple:

    `M = (Q, Σ, δ, q₀, F)`

    | Symbol | Meaning |
    |--------|---------|
    | **Q** | Set of all states |
    | **Σ** | Input alphabet |
    | **δ** | Transition function |
    | **q₀** | Start state |
    | **F** | Set of final states |
    """)

    st.markdown("---")
    st.markdown("### This ATM's DFA")
    st.markdown(f"""
    - **Q** = {{q0, q1, q2, q3, q4, q5, q6, qD}}
    - **Σ** = 8 input symbols
    - **q₀** = q0 (Idle)
    - **F** = {{q6}} (Session Complete)
    - **Dead** = qD (Error/Blocked)
    """)

    st.markdown("---")
    st.markdown("### States Legend")
    for sid, label in STATES.items():
        color = "#ff4b2b" if sid == DEAD_STATE else ("#38ef7d" if sid in FINAL_STATES else "#0072ff")
        st.markdown(
            f'<span style="color:{color}; font-family:monospace; font-weight:700;">{sid}</span>'
            f' — {label}',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("**Demo PIN:** `1234`")
    st.markdown("**Starting Balance:** `PKR 50`")

    st.markdown("---")
    st.caption("SMIU | BSDS | Theory of Automata")