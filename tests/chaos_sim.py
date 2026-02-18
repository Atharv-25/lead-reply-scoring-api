import time
import json
from reply_intelligence import ReplyIntelligence

# Initialize Analyzer
analyzer = ReplyIntelligence()

# ─── THE 15 CHAOTIC LEADS ───
# Format: (Day, Body) — Day 1 is "10 days ago", Day 10 is "Today".
scenarios = {
    "lead1_ghost_panic": [ # Starts hot, ghosts, comes back urgent
        (1, "We are evaluating Apollo and ZoomInfo. Need a third option."),
        (2, "Can you share pricing?"),
        # Ghosting Days 3-8...
        (9, "Hey sorry missed this. effectively immediately our contract is up. NEED PRICING NOW.") 
    ],
    "lead2_budget_juggler": [ # No budget -> Found money
        (1, "Looks cool but budgets are frozen for Q1."),
        (3, "Might have some wiggle room if its under $10k."),
        (5, "Actually, CFO just approved a small pilot budget."),
        (8, "Can we sign by Friday?")
    ],
    "lead3_competitor_shopper": [ # Heavy compare, goes silent, reappears
        (1, "How do you compare to Apollo?"),
        (2, "They have better data coverage it seems."),
        (5, "I like your UI better though."),
        # Silence...
        (10, "Ok we are dropping Apollo. Send contract.")
    ],
    "lead4_tech_stickler": [ # Deep tech Qs -> Silence (Cooling trap)
        (1, "Does your API support bulk enrichment via webhook?"),
        (2, "Send me the docs."),
        (3, "I don't see the rate limits documented."),
        # Silence...
    ],
    "lead5_busy_exec": [ # Typos, short, high intent
        (1, "intrstd. send deck."),
        (2, "price?"),
        (4, "too high. can u do 5k?"),
        (6, "ok send it.")
    ],
    "lead6_skeptic": [ # Argues -> Converts
        (1, "I doubt your data is better than what we have."),
        (3, "Sent you a test list. Verify it."),
        (5, "Results were actually decent. Surprising."),
        (7, "Let's talk.")
    ],
    "lead7_delegator": [ # Slow, looping people in
        (1, "Looping in my ops lead."),
        (4, "cc'ing my VP."),
        (8, "My team likes this. What's next steps?")
    ],
    "lead8_pure_ghost": [ # High starts, then dies (Should rot)
        (1, "We are ready to buy. Send invoice."),
        # Total silence...
    ],
    "lead9_tire_kicker": [ # Asking random feature Qs, no buying signals
        (1, "Do you have a darker mode?"),
        (4, "Can I change the font size?"),
        (8, "Does it integrate with Asana?")
    ],
    "lead10_urgent_mess": [ # All caps, panic, flake
        (1, "WE NEED LEADS YESTERDAY."),
        (2, "CALL ME."),
        # Flakes...
        (9, "WHERE ARE YOU?")
    ],
    "lead11_polite_no": [ # Rejection -> Pivot
        (1, "Thanks but we are set."),
        (5, "Actually our provider just crashed."),
        (6, "Can we talk?")
    ],
    "lead12_wrong_guy": [ # Referral
        (1, "Not me."),
        (3, "Talk to Sarah."),
        # Sarah replies in same thread? Or he fwd? Let's say he replies for her.
        (4, "Sarah here. I'm interested.") 
    ],
    "lead13_ooo_loop": [ # Auto replies (noise) -> Real signal
        (1, "Automatic reply: OOO until Monday."),
        (3, "Automatic reply: OOO until Monday."),
        (5, "Back now. This looks interesting.")
    ],
    "lead14_enterprise_slog": [ # Slow, formal, high value
        (1, "Attached is our security questionnaire."),
        (6, "Legal is reviewing."),
        (10, "Approved. Send MSA.")
    ],
    "lead15_fanboy": [ # Fan, no budget (Time waster / Low priority)
        (1, "Love your LinkedIn posts!"),
        (3, "Great content."),
        (7, "Would love to pick your brain sometime.")
    ]
}

print("\n🔥 REAL-WORLD CHAOS SIMULATION (10 DAYS)")
print("Objective: Verify Ranking Order Integrity Daily")
print("=================================================")

# Simulation Loop
for current_day in range(1, 11):
    print(f"\n📅 DAY {current_day}")
    daily_snapshot = []
    
    for lead_id,msgs in scenarios.items():
        # Build history for this lead up to current_day
        history = []
        messages_so_far = [m for m in msgs if m[0] <= current_day]
        
        if not messages_so_far:
            continue
            
        # Construct message objects with simulated timestamps
        # Current time = Day X (say 5PM).
        # Message Day Y = (X - Y) days ago.
        
        current_time = time.time()
        
        for day, body in messages_so_far:
            days_ago = current_day - day
            # Add some jitter/hours variability for realism
            timestamp = current_time - (days_ago * 86400) 
            history.append({
                "role": "user", # or whatever server expects, reply_intelligence expects 'sender': 'lead'
                "sender": "lead",
                "body": body,
                "timestamp": timestamp
            })
            
        # Analyze
        result = analyzer.analyze_thread(history)
        score = result['score']
        band = result['state']
        mom = result['momentum']
        decay = result.get('cooling_decay', 0)
        
        daily_snapshot.append({
            "lead": lead_id,
            "score": score,
            "band": band,
            "mom": mom,
            "decay": decay,
            "last_msg": messages_so_far[-1][1][:30] + "..."
        })
        
    # RANK by Score (Desc)
    daily_snapshot.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"{'Rank':<4} {'Score':<6} {'Band':<12} {'Mom.':<8} {'Decay':<6} {'Lead ID':<25} {'Last Msg'}")
    print("-" * 100)
    for i, lead in enumerate(daily_snapshot):
        # Visual check helpers
        flag = ""
        if i < 3 and lead['score'] < 30: flag = "⚠️ LOW TOP?"
        if i > 10 and lead['score'] > 60: flag = "⚠️ BURIED HIGH?"
        
        print(f"#{i+1:<3} {lead['score']:<6} {lead['band']:<12} {lead['mom']:<8} -{lead['decay']:<5} {lead['lead']:<25} {lead['last_msg']} {flag}")

print("\n\n✅ SIMULATION COMPLETE")
