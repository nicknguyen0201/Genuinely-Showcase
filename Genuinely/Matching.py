#!/usr/bin/env python
# coding: utf-8

# In[1]:


from numpy.linalg import norm
import numpy as np
import json
import sys
import requests
from collections import defaultdict
import random
import matplotlib.pyplot as plt
import os
from supabase import create_client
from datetime import datetime, timezone
from typing import Dict, Tuple, List, Any
import dotenv
from dotenv import load_dotenv
from collections import defaultdict
import time
from datetime import datetime, timezone, timedelta


# In[2]:


load_dotenv("../.env.local")


# In[3]:


def get_preference_matrix(X):
    """
   take in matrix of MSE that correspond to user index

   sort the index based on mse
   put the indices of users into pref matrix
    """
    n= X.shape[0]
    pref_matrix = np.zeros((n, n), dtype=int)
    for i in range(n):
        sims = X[i].copy()
        sims[i] = -np.inf # force self to the end
        # Back when I was using cosine sim (larger cos , closer ppl), sort others by descending similarity, stable for deterministic ties.
        # Now I am using mse, which mean the smaller the mse, the closer 2 people, so sort by acsending
       
        sorted_idx = np.argsort(sims)  # length n, includes i
        # remove self explicitly (robust even if ties get weird)
        sorted_idx = sorted_idx[sorted_idx != i]       # length n-1
        # fill row: others first, then self at the end
        pref_matrix[i, :-1] = sorted_idx
        pref_matrix[i, -1] = i
    return pref_matrix



# In[ ]:





# In[ ]:





# In[4]:


#MIT License from szhangbi repo Works-on-Irving-s-algorithm
ENABLE_PRINT = 0
DETAILED_ENABLE_PRINT=0
#convert the preference matrix into ranking matrix
def get_ranking(preference):
    ranking = np.zeros(preference.shape,dtype=int)
    for row in range(0,len(preference[:,0])):
        for col in range(0,len(preference[0,:])):
            ranking[row,col]=list(preference[row,:]).index(col)
    return ranking


def phaseI_reduction(preference, leftmost, rightmost, ranking):
    ## leftmost and rightmost is updated here
    set_proposed_to=set() ## this set contains the players who has been proposed to and holds someone
    for person in range(0,len((preference[0,:]))):
        proposer = person
        while True:
            next_choice = preference[proposer,leftmost[proposer]]
            current = preference[next_choice,rightmost[next_choice]]

            while ranking[next_choice,proposer]> ranking[next_choice,current]:
                ## proposer proposed to his next choice but being rejected
                if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print("player", proposer+1, "proposed to", next_choice+1, "; ", next_choice+1, "rejects", proposer+1 )
                leftmost[proposer] = leftmost[proposer] + 1 ##proposer's preference list got reduced by 1 from the left
                next_choice = preference[proposer, leftmost[proposer]]
                current = preference[next_choice, rightmost[next_choice]]

            ## proposer being accepted by his next choice and next choice rejected his current partner
            if current!= next_choice: ##if next choice currently holds somebody
                if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print("player", proposer + 1, "proposed to", next_choice + 1,"; ",next_choice + 1, "rejects", current + 1, " and holds", proposer+1 )
                leftmost[current]=leftmost[current]+1
            else: ##if next choice currently holds no body
                if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print("player", proposer + 1, "proposed to", next_choice+1, "; ", next_choice+1, "holds", proposer+1)

            rightmost[next_choice] = ranking[next_choice, proposer] ##next choice's preference's list got reduced, rightmost is proposer now

            if not (next_choice in set_proposed_to): ##if no one is rejected <=> next choice has not been proposed before proposer proposed
                break
            proposer = current ##the one who being rejected is the next proposer
        set_proposed_to.add(next_choice)

    soln_possible = not (proposer==next_choice)
    ##Claim1: if there is a player i who is rejected by all, then he must be the last proposer in the loop
    ##Proof: bc if someone who has not proposed anyone, then there must be at least 1 person besides player i who holds nobody
    ##This fact is used to decide whether the solution exists or not

    #if soln_possible:
    if ENABLE_PRINT:  print("The table after phase-I execution is:")
    if ENABLE_PRINT:  friendly_print_current_table(preference, leftmost, rightmost)
    return soln_possible, leftmost, rightmost

def get_all_unmatched(leftmost, rightmost):
    unmatched_players = []
    for person in range(0, len(leftmost)):
        if leftmost[person] != rightmost[person]:
            if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print(person + 1, "is unmatched")
            unmatched_players.append(person)
    return unmatched_players


def update_second2(person,preference, second, leftmost, rightmost, ranking):
    second[person]=leftmost[person]+1 #before updation, second is simply leftmost +1
    pos_in_list = second[person]
    while True:  # a sophisticated way to update the second choice, as some person between leftmost and rightmost might be dropped as well
        next_choice = preference[person, pos_in_list]
        pos_in_list += 1
        if ranking[next_choice, person] <= rightmost[next_choice]:  # check whether person is still in next_choice's reduced list <=> next_choice is still in his list
            second[person] = pos_in_list -1
            return next_choice, second


##Claim2: if a person whose reduced list contains only one person, he shall not appear in the cycle?
##Proof: Assume person i's list only contains one person j, -> j holds i's proposal after the reduction
# if there is l behind i in j's list, he must be deleted from i's list
# if there is k before i in j's list, then j's proposal must be accepted by someone a other than i, a's proposal must be accepted by someone b other than i,j,
#   b's proposal must be accepted by someone c other than a,i,j ... since there is only finite players, contradiction
#->i is the only person in j's reduced list -> i,j won't be found by find_unmatched and won't be someone's last choice or second choice

##Claim3: if a person whose reduced list contains more than one person, he must appear in the cycle?
##Proof: False. Duplicate the preference matrix in the paper with each number +6, and put the last six person at the end of the list of the first six person,
# and put the first six person at the end of the list of the last six person


##This fact means that we only need to initialize cycle once and loop to reduce the element of it


def seek_cycle2(preference, second,  first_unmatched, leftmost, rightmost, ranking):
    #tail= set()
    #print("I am in seek_cycle2")
    cycle =[]
    posn_in_cycle = 0
    person = first_unmatched
    if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print("p_",posn_in_cycle+1,":",person+1)

    while not (person in cycle): ##loop until the first repeat
        cycle.append(person)
        posn_in_cycle+=1
        next_choice, second = update_second2(person,preference, second, leftmost, rightmost, ranking)
        if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print("q_",posn_in_cycle,":",next_choice+1)
        person = preference[next_choice,rightmost[next_choice]]
        if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print("p_",posn_in_cycle+1,":",person+1)
    #after this loop, person is the one who repeats first

    last_in_cycle= posn_in_cycle-1 #position of the last one in cycle in the "cycle" list
    #tail = set(cycle) #using the set object in Python, we don't need cycle_set
    while True: #this is used to find the head of the cycle and its position in the "cycle" list
        posn_in_cycle = posn_in_cycle - 1
        #tail = tail.remove(cycle[posn_in_cycle])
        if cycle[posn_in_cycle]==person: #loop until we get the person who repeat first
            first_in_cycle = posn_in_cycle
            break
    #print("!!!",first_in_cycle,last_in_cycle)
    #print("I am out of seek_cycle2 now")
    friendly_print_rotation(cycle, first_in_cycle, last_in_cycle, preference, leftmost, second)
    return first_in_cycle, last_in_cycle, cycle, second



def phaseII_reduction2(preference, first_in_cycle, last_in_cycle, second, leftmost, rightmost,  soln_possible, cycle):
    #print("I am in phase ii reduction2")
    #print("input is:")
    #print([ leftmost, rightmost, second])
    for rank in range(first_in_cycle, last_in_cycle+1):
        proposer = cycle[rank]
        leftmost[proposer] = second[proposer]
        second[proposer] = leftmost[proposer]+1 #it is mentioned that proper initialization is unnecessary
        next_choice = preference[proposer,leftmost[proposer]]
        if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print(proposer+1, "proposed to his second choice in the reduced list:", next_choice+1, ";", next_choice+1,"accepted ", proposer+1, "and rejected", preference[next_choice,rightmost[next_choice]]+1 )
        rightmost[next_choice] = get_ranking(preference)[next_choice,proposer]
    #print([leftmost, rightmost, second])
    #To check whether stable matching exists or not#
    rank = first_in_cycle
    while (rank <= last_in_cycle) and soln_possible:
        proposer = cycle[rank]
        soln_possible = leftmost[proposer] <= rightmost[proposer]
        rank+=1
    if not soln_possible:
        if ENABLE_PRINT: print("No stable matching exists!!!")
        return soln_possible, first_in_cycle, last_in_cycle, second.copy(), leftmost.copy(), rightmost.copy(),  cycle

    #A special step to handle the case of more than one cycle, seems not contained in the code in paper#
    for person in range(first_in_cycle, last_in_cycle):
        if leftmost[cycle[first_in_cycle]] != rightmost[cycle[first_in_cycle]]:
            to_print =np.array(cycle[first_in_cycle:last_in_cycle + 1])+1
            if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print("E=",to_print, "is still unmatched")
            if ENABLE_PRINT: print("The table after rotation elimination is:")
            if ENABLE_PRINT:  friendly_print_current_table(preference, leftmost, rightmost)
            return soln_possible, first_in_cycle,  last_in_cycle,  second.copy(), leftmost.copy(), rightmost.copy(),  cycle
    to_print = np.array(cycle[first_in_cycle:last_in_cycle + 1]) + 1
    if ENABLE_PRINT and DETAILED_ENABLE_PRINT: print("E=",to_print, "is all  matched")
    first_in_cycle=0

    #print("I am out of phase II reduction2 now")
    if ENABLE_PRINT: print("The table after rotation elimination is:")
    if ENABLE_PRINT:  friendly_print_current_table(preference, leftmost, rightmost)
    return soln_possible, first_in_cycle, last_in_cycle, second.copy(), leftmost.copy(), rightmost.copy(),  cycle

def friendly_print_current_table(preference, leftmost, rightmost):
    for person in range(0,len(preference)):
        to_print = []
        for entry in range(leftmost[person],rightmost[person]+1):
            if get_ranking(preference)[preference[person, entry],person]<=rightmost[preference[person,entry]]:
                to_print.append(preference[person,entry])
        to_print=np.array(to_print)
        print(person+1,"|",to_print+1)

def friendly_print_rotation(cycle,first_in_cycle,last_in_cycle, preference,leftmost,second):
    print("The rotation exposed is:")
    print("E| H S")
    for person in range(first_in_cycle,last_in_cycle+1):
        print("{0}| {1} {2}".format(cycle[person]+1,preference[cycle[person],leftmost[cycle[person]]]+1,preference[cycle[person],second[cycle[person]]]+1))

def friendly_print_sol(partners):
    seen = []
    pairs=[]
    to_print = []
    for sol in partners:
        for people in range(0, len(sol)):
            if people not in seen:
                seen.append(people)
                pairs.append((people+1,sol[people]+1))
                seen.append(sol[people])
        to_print.append(pairs)
        pairs = []
        seen=[]
    return to_print


def Find_all_Irving_partner(preference):

    ranking = get_ranking(preference)
    leftmost = np.zeros(len(preference[0, :]), dtype=int) #leftmost indicates the position of the person who holds i's proposal
    second = np.zeros(len(preference[0, :]), dtype=int) + 1
    rightmost = np.zeros(len(preference[0, :]), dtype=int) + len(preference[0,:]) - 1 #rightmost indicates the position of the person whose proposal i holds
    partner = np.zeros(len(preference[0, :]), dtype=int)
    soln_possible = False
    first_unmatched = 1
    first_in_cycle = 0
    last_in_cycle = 0
    cycle=[]
    partners = []
    soln_found = False

    if ENABLE_PRINT: print("The preference lists are:")
    if ENABLE_PRINT: print(preference+1)


    soln_possible, leftmost, rightmost = phaseI_reduction(preference, leftmost, rightmost, ranking)
    if not soln_possible:
        if ENABLE_PRINT: print("No stable matching exists!!")
        return partners
    second = leftmost + 1



    seen = []
    queue =[]
    qlfmost =leftmost.copy()
    qrtmost = rightmost.copy()
    qsecond = second.copy()
    seen.append([qlfmost,qrtmost, qsecond])
    queue.append([qlfmost,qrtmost, qsecond])
    while queue:
        [qlfmost, qrtmost, qsecond] = queue.pop(0)

        unmatched = get_all_unmatched(qlfmost, qrtmost)
        if unmatched:
            # if ENABLE_PRINT: print("The tripple is:")
            # if ENABLE_PRINT: print([qlfmost, qrtmost, qsecond])
            # if ENABLE_PRINT: print("it is unmatched yet!")
            for person in unmatched:
                if ENABLE_PRINT: print("person is:", person+1)
                #print("before skcycle:",[qlfmost, qrtmost, qsecond])
                first_in_cycle, last_in_cycle, cycle, cursecond = seek_cycle2(preference, qsecond.copy(), person, qlfmost.copy(), qrtmost.copy(), ranking)
                #print("after skcycle:", [qlfmost, qrtmost, qsecond])
                soln_possible, first_in_cycle, last_in_cycle, cursecond,  curlfmost,  currtmost, cycle = phaseII_reduction2(preference, first_in_cycle, last_in_cycle, cursecond.copy(), qlfmost.copy(), qrtmost.copy(), soln_possible, cycle)
                #print("The tripple is:")
                #print([curlfmost, currtmost, cursecond])
                curtripple = [curlfmost, currtmost, cursecond]
                if not any(all((pref1==pref2).all() for pref1, pref2 in zip(curtripple,tripple)) for tripple in seen) and soln_possible:
                    # if ENABLE_PRINT: print("The new tripple is:")
                    # if ENABLE_PRINT: print([curlfmost, currtmost, cursecond])
                    # if ENABLE_PRINT: print("it is added to the queue")
                    seen.append([curlfmost, currtmost, cursecond])
                    queue.append([curlfmost, currtmost, cursecond])
                #print("after phase ii:", [qlfmost, qrtmost, qsecond])
        else:
            # if ENABLE_PRINT: print("The tripple is:")
            # if ENABLE_PRINT: print([qlfmost, qrtmost, qsecond])
            # if ENABLE_PRINT: print("it is matched already!")
            partner = np.zeros(len(preference[0, :]), dtype=int)
            for person in range(0, len(qlfmost)):
                partner[person] = preference[person, qlfmost[person]]
            if not any(partner.tolist() == p for p in partners):
                partners.append(partner.tolist())

            to_print = friendly_print_sol(partners)


    if ENABLE_PRINT: print("The solution is: ", to_print)
    return partners


# In[5]:


EMAIL_SLEEP_SECONDS = 1.0  # <= 2 req/sec safe


# In[6]:


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
RESEND_FROM = os.environ["RESEND_FROM"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# In[7]:


print(RESEND_FROM)


# In[8]:


unlearned_weight=[100,100,100,100,
                  50,50,50,50,50,50,
                 1,1,1,1,1,1,
                 3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]
PENALTY=300


# In[9]:


def get_rows_supabase():
    resp = (
        supabase.table("profiles")
        .select("id,name,email,survey_vec,active")
        .eq("active", True)
        .eq("agreed_to_terms", True)
        .execute()
    )

    rows = resp.data or []
    if not rows:
        print("⚠️  No rows returned from Supabase.")
        return np.empty((0, len(unlearned_weight))), [], {}

    # --- filter + validate vectors ---
    clean = []
    for r in rows:
        vec = r.get("survey_vec")
       
        if isinstance(vec, list) and len(vec) == len(unlearned_weight):
            clean.append(r)
        else:
            print(f"⚠️  Skipping user {r.get('name','?')} due to bad vector length.")

    if not clean:
        raise ValueError(f"No valid vectors of length {len(unlearned_weight)} found.")
    #print(clean)
    return clean


# In[10]:


def get_X_ids_and_namemap():
    
   
    """
    1. Fetch valid profile rows from Supabase.
    2. Stack their survey_vec into a matrix F (n_users × d_dims).
    3. Build a user-by-user matrix X where
         X[i, j] = sum_k w_k * (x_{ik} - x_{jk})^2
       using the global weight vector w.
    4. Return X, ids, and an index→id map.
    """
    # 1) Get cleaned rows (already filtered + validated)
    clean_rows = get_rows_supabase()
    n = len(clean_rows)

    # 2) Stack survey_vec into F of shape (n, d)
    F = np.array([r["survey_vec"] for r in clean_rows], dtype=float)  # each row = user vector
    n, d = F.shape

    # 3) Make sure weight vector matches dimension d
    w_arr = np.array(unlearned_weight, dtype=float)  # use global w
    if w_arr.shape[0] != d:
        raise ValueError(f"Weight vector length {w_arr.shape[0]} != feature dim {d}")

        
    #Collect ids in row order
    ids = [r["id"] for r in clean_rows]

    # Build index -> id map (useful after stable_roommate)
    id_to_info = {
        r["id"]: (
            (r.get("name") or "").strip(), 
            (r.get("email") or "").strip(),
            index,)
        for index, r in enumerate(clean_rows)
    }
     # -------------------------------
    # ADD DUMMY USER ONLY IF n IS ODD
    # -------------------------------
    add_dummy = (n % 2 == 1)
    if add_dummy:
        dummy_vec = np.zeros((1, d), dtype=float)
        F = np.vstack([F, dummy_vec])      # F becomes (n+1, d)
        ids.append(DUMMY_ID)               # keep index alignment
        id_to_info[DUMMY_ID] = ("<DUMMY>", "<NO EMAIL>",-1)

        n += 1  # optional: keep n consistent (or just re-read n, d = F.shape) 

        
    # 4) Compute pairwise differences: (x_i - x_j) for all i,j.
    #    F[:, None, :] -> (n, 1, d)
    #    F[None, :, :] -> (1, n, d)
    #    Broadcasting gives (n, n, d)
    diffs = F[:, None, :] - F[None, :, :]  # shape (n, n, d)

    # 5) Square them: (x_i - x_j)^2
    sq_diffs = diffs ** 2  # shape (n, n, d)

    # 6) Apply weights per dimension and sum over d.
    #    w_arr has shape (d,), broadcast to (n, n, d)
    #    result is (n, n) matrix of scalar scores.
    X = (sq_diffs * w_arr).sum(axis=2)  # shape (n, n)



    return X, ids, id_to_info


# In[41]:


def fetch_past_pairs(supabase, limit=100000):
    """
    Returns a set of canonical pairs {(low, high), ...} for all previously created matches.
    """
    resp = (
        supabase.table("matches")
        .select("user_low,user_high")
        .limit(limit)
        .execute()
    )
    if not resp.data:
        return set()

    banned = set()
    for row in resp.data:
        a = row["user_low"]
        b = row["user_high"]
        if a and b and a != b:
            low, high = (a, b) if a < b else (b, a)
            banned.add((low, high))
    #print(len(banned))
    return banned


# In[12]:


def apply_ban_penalty_inplace(X, ids_to_info, banned_pairs):
    """
    Modifies X in-place:
      for each banned (a,b), set X[i,j] and X[j,i] to a huge value.
      I let penalty =200 because it is worse to have the same match again than match with who you not prefer
    """
    

    for low, high in banned_pairs:
        if low not in ids_to_info or high not in ids_to_info:
            continue
        _, _, i = ids_to_info[low]
        _, _, j = ids_to_info[high]
        X[i, j] = PENALTY
        X[j, i] = PENALTY


# In[13]:


def all_matchings_to_ids(sol, ids):
    """
    Convert an index-based matching solution into a list of (id1, id2) tuples.
    sol : list[int] - partner indices for each user
    ids : list[str] - user IDs in same order as matrix X
    """
    #print(sol)
    #print(ids)
    assert len(sol) == len(ids)
    
    pairs = []
    seen = set()
    for i, p in enumerate(sol):
        pair = tuple(sorted((ids[i], ids[p])))
        if pair not in seen:
            pairs.append(pair)
            seen.add(pair)
    return pairs


# In[14]:


def check_match_results(res_pairs, ids_to_info):
    """
    Print human-readable match results.

    Parameters
    ----------
    res_pairs : list[tuple[str,str]]
        Each tuple is (user_id_A, user_id_B)
    id_to_info : dict[str, tuple[str,str]]
        From get_X_ids_and_namemap() → { id: (name, email) }
    """
    if not res_pairs:
        print("⚠️  No matches to display.")
        return

    print("\n🧩 Match Results (Human-readable):\n")
    for a, b in res_pairs:#ignore index
        # 🚫 Skip dummy matches
        if a not in ids_to_info or b not in ids_to_info:
            continue
        name_a, email_a, _ = ids_to_info[a]
        name_b, email_b, _ = ids_to_info[b]
        print(f"{name_a:<12} ({email_a:<25})  ↔  {name_b:<12} ({email_b})")


# In[15]:


DUMMY_ID = "__DUMMY__"  # if you used one in-memory


# In[16]:


def canon_pair(a: str, b: str):
    return (a, b) if a < b else (b, a)

"""Redundant, already in the  send email and mark()"""

def insert_matches(res_pairs, round_id: str):
    # 1) Remove dummy
    real_pairs = [(a, b) for (a, b) in res_pairs if a != DUMMY_ID and b != DUMMY_ID]

    # 2) Canonicalize low/high to match DB constraint
    rows = []
    for a, b in real_pairs:
        low, high = canon_pair(a, b)
        rows.append({
            "user_low": low,
            "user_high": high,
            "round_id": round_id,
            # emailed_at stays NULL until you successfully send emails
        })

    if not rows:
        print("[matches] nothing to insert (maybe everyone matched dummy).")
        return

    # 3) Idempotent write: safe to re-run
    resp = supabase.table("matches").upsert(
        rows,
        on_conflict="round_id,user_low,user_high"
    ).execute()

    print(f"[matches] upserted {len(rows)} rows for round {round_id}")
    return resp
# In[17]:


def send_email_resend(to_email: str, subject: str, html: str):
    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": RESEND_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html,
        },
        timeout=20,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Resend error {r.status_code}: {r.text}")
    return r.json()




# In[18]:


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )

def build_match_email_html(
    match_name: str,
    match_email: str,
    match_gender: str,
    match_year: str,
    common_things: list[str],
) -> str:
    common_list_html = "".join(f"<li>{esc(item)}</li>" for item in common_things)

    return f"""
<div style="
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
  line-height: 1.5;
  font-size: 1rem;
">
  <h2 style="margin: 0 0 0.75em;">Your UCSD match</h2>

  <div style="
    border: 0.0625em solid #e5e7eb;
    border-radius: 0.75em;
    padding: 1em;
    background: #fafafa;
  ">
  <p style="
    margin: 0;
    font-size: 0.875em;
    color: #374151;
  ">
    <strong>Safety reminder:</strong>
    Genuinely facilitates introductions only and does not supervise interactions.
    Please meet in public places and use your own judgment when connecting with others.
  </p>
    <p style="margin: 0 0 0.5em;"><strong>Name:</strong> {esc(match_name)}</p>
    <p style="margin: 0 0 0.5em;"><strong>Gender:</strong> {esc(match_gender)}</p>
    <p style="margin: 0 0 0.75em;"><strong>Year:</strong> {esc(match_year)}</p>

    <p style="margin: 0 0 0.75em;">
      <strong>Email:</strong>
       <span style="font-family: monospace;">
            {esc(match_email)}
      </span>
    </p>

    <p style="margin: 0 0 0.75em; font-size: 0.95em;">
      You can use this email to reach out, say hi, and coordinate a meetup if you’d like.
      A short intro is totally fine.
    </p>

    <p style="margin: 0 0 0.5em;"><strong>Things you have in common:</strong></p>

    <ul style="margin: 0; padding-left: 1.25em;">
      {common_list_html}
    </ul>
   

  
  </div>
 
    <p style="margin: 1em 0 0; color: #6b7280; font-size: 0.875em;">
    Tip: “Hey, I think we got matched on Genuinely — want to grab coffee at Price sometime this week?”
   
  You’re receiving this because you’re an active Genuinely user.<br />
  To stop receiving emails, log in to your dashboard and click “Pause matching.”
    </p>
</div>
""".strip() 


# In[19]:


GENDER_OPTIONS = ["male", "female", "non-binary", "other"]
YEAR_OPTIONS = ["freshman", "sophomore", "junior", "junior-transfer", "senior", "grad"]

VIBE_QUESTIONS = [
    "Introvert",
    "Extrovert",
    "Spontaneous",
    "Planner",
    "Indoor",
    "Adventurous",
]

INTEREST_QUESTIONS = [
    "Study together",
    "Gaming",
    "Eat out / cooking",
    "Explore San Diego",
    "Shopping / fashion",
    "Chill hangouts",
    "Partying",
    "Music",
    "Fitness",
    "UCSD typicals",
    "Art / drawing",
    "Anime",
    "Movies",
    "Outdoor activities",
    "Entrepreneurship",
    "Tech",
]


def decode_survey_vector(vec: List[int]) -> Dict[str, Any]:
    if len(vec) != 33:
        raise ValueError(f"Expected vector of length 33, got {len(vec)}")

    i = 0

    # ---- Gender (4 dims, one-hot) ----
    gender_slice = vec[i : i + 4]
    i += 4
    gender = (
        GENDER_OPTIONS[gender_slice.index(1)]
        if 1 in gender_slice
        else "Unknown"
    )

    # ---- Year (6 dims, one-hot) ----
    year_slice = vec[i : i + 6]
    i += 6
    year = (
        YEAR_OPTIONS[year_slice.index(1)]
        if 1 in year_slice
        else "Unknown"
    )

    # ---- Vibes (6 dims, binary) ----
    vibe_slice = vec[i : i + 6]
    i += 6
    vibes = {
        label: bool(bit)
        for label, bit in zip(VIBE_QUESTIONS, vibe_slice)
    }

    # ---- Interests (16 dims, binary) ----
    interest_slice = vec[i : i + 16]
    i += 16
    interests = {
        label: bool(bit)
        for label, bit in zip(INTEREST_QUESTIONS, interest_slice)
    }

    # ---- Bias (last dim) ----
    bias = vec[i]  # always 1, but we don’t need it

    return {
        "gender": gender,
        "year": year,
        "vibes": vibes,
        "interests": interests,
    }


# In[20]:


def common_things_from_vectors(vec_a: List[int], vec_b: List[int]) -> List[str]:
    A = decode_survey_vector(vec_a)
    B = decode_survey_vector(vec_b)

    commons: List[str] = []

    # Same year / gender
    if A["year"] != "Unknown" and A["year"] == B["year"]:
        commons.append(f"Both are {A['year'].replace('-', ' ').title()} at UCSD")

    if A["gender"] != "Unknown" and A["gender"] == B["gender"]:
        commons.append(f"Both identify as {A['gender'].title()}")

    # Shared vibes (only include the ones both said yes to)
    for vibe in VIBE_QUESTIONS:
        if A["vibes"].get(vibe) and B["vibes"].get(vibe):
            commons.append(f"Both are {vibe.lower()}")

    # Shared interests
    for interest in INTEREST_QUESTIONS:
        if A["interests"].get(interest) and B["interests"].get(interest):
            commons.append(f"Both like {interest}")

    # De-dupe while preserving order + cap
    seen = set()
    out = []
    for item in commons:
        if item not in seen:
            seen.add(item)
            out.append(item)
       
    return out


# In[21]:


"""avoid being flag for spam by email by including another email directly"""
def obfuscate_email(email: str) -> str:
    if not email:
        return ""
    return email.replace("@", " [at] ").replace(".", " ")


# In[50]:


from datetime import datetime, timezone
from typing import Dict, Tuple, Any, List

def send_matches_and_mark(res_pairs, ids_to_info: Dict[str, Tuple[str, str]], round_id: str):
    """
    Sends 2 match emails per pair using decoded survey vectors:
      - Email to A contains B’s details + “things in common”
      - Email to B contains A’s details + “things in common”

    DB behavior:
      - Ensures a match row exists via UPSERT (round_id, user_low, user_high)
      - Writes user_low_name, user_high_name, compatibility_reasons (snapshot)
      - Sets matches.emailed_at ONLY after both emails succeed.

    IMPORTANT: ids_to_info MUST map user_id -> (name, email).
    """

    now_iso = datetime.now(timezone.utc).isoformat()

    # Cache profiles lookups so we don't hit DB 2x per pair
    profile_cache: Dict[str, Dict[str, Any]] = {}

    def load_profile(uid: str) -> Dict[str, Any]:
        if uid in profile_cache:
            return profile_cache[uid]

        resp = (
            supabase.table("profiles")
            .select("id,email,name,survey_vec")
            .eq("id", uid)
            .maybe_single()
            .execute()
        )

        if not resp.data:
            raise RuntimeError(f"Profile not found for uid={uid}")

        profile_cache[uid] = resp.data
        return resp.data

    def list_to_reason_text(items: List[str]) -> str:
        """
        Store compatibility reasons as a single text field (matches.compatibility_reasons).
        Keep it human-readable + stable.
        """
        items = [x.strip() for x in items if x and x.strip()]
        if not items:
            return ""
        # Compact bullet-ish text (works great for DB + dashboard)
        return " • " + " • ".join(items)

    
    for a, b in [(x, y) for (x, y) in res_pairs if x != DUMMY_ID and y != DUMMY_ID and x != y]:
        # ids_to_info: uid -> (name, email)
        name_a, email_a,_ = ids_to_info.get(a, ("", "",""))
        name_b, email_b,_ = ids_to_info.get(b, ("", "",""))

        if not email_a or not email_b:
            print(f"[email] skipping pair missing email: {a}={email_a}, {b}={email_b}")
            continue

        low, high = canon_pair(a, b)

        # Names must correspond to low/high ordering for snapshot fields
        if low == a:
            low_name = (name_a or "").strip()
            high_name = (name_b or "").strip()
        else:
            low_name = (name_b or "").strip()
            high_name = (name_a or "").strip()
        """
        # Idempotency: skip if already emailed this round
        existing = (
            supabase.table("matches")
            .select("emailed_at")
            .eq("round_id", round_id)
            .eq("user_low", low)
            .eq("user_high", high)
            .maybe_single()
            .execute()
        )
        

        if existing.data and existing.data.get("emailed_at"):
            print(f"[email] already emailed pair {email_a} <-> {email_b}, skipping")
            continue
        """

        subj = f"Your UCSD match is here (Round {round_id})"

        try:
            # Load survey vectors for decoding
            prof_a = load_profile(a)
            prof_b = load_profile(b)

            vec_a = prof_a["survey_vec"]
            vec_b = prof_b["survey_vec"]

            dec_a = decode_survey_vector(vec_a)
            dec_b = decode_survey_vector(vec_b)

            # “Things in common” (same list can be used for both directions)
            commons = common_things_from_vectors(vec_a, vec_b)
            if not commons:
                commons = ["Both are UCSD students", "Both opted in for matching this round"]

            # Store in DB as a text snapshot (derived from the same list used in email HTML)
            reasons_text = list_to_reason_text(commons)

            # Ensure match row exists + snapshot fields are saved (idempotent)
            # NOTE: requires a UNIQUE constraint for ON CONFLICT to work.
            # You already have: unique (round_id, user_low, user_high)
          
            (
                supabase.table("matches").upsert(
                    {
                        "round_id": round_id,
                        "user_low": low,
                        "user_high": high,
                        "user_low_name": low_name,
                        "user_high_name": high_name,
                        "compatibility_reasons": reasons_text,
                        # don't set emailed_at here; only after email success
                    },
                    on_conflict="round_id,user_low,user_high",
                )
                .execute()
            )
  

            # Email to A about B
            html_a = build_match_email_html(
                match_name=(name_b or prof_b.get("name") or "").strip(),
                match_email=email_b,
                match_gender=dec_b["gender"].title() if dec_b.get("gender") and dec_b["gender"] != "Unknown" else "Unknown",
                match_year=dec_b["year"].replace("-", " ").title() if dec_b.get("year") and dec_b["year"] != "Unknown" else "Unknown",
                common_things=commons,  # ✅ same data as stored reasons_text
            )

            # Email to B about A
            html_b = build_match_email_html(
                match_name=(name_a or prof_a.get("name") or "").strip(),
                match_email=email_a,
                match_gender=dec_a["gender"].title() if dec_a.get("gender") and dec_a["gender"] != "Unknown" else "Unknown",
                match_year=dec_a["year"].replace("-", " ").title() if dec_a.get("year") and dec_a["year"] != "Unknown" else "Unknown",
                common_things=commons,  # ✅ same data as stored reasons_text
            )

            # Send both emails
            send_email_resend(email_a, subj, html_a)
            time.sleep(EMAIL_SLEEP_SECONDS)
            send_email_resend(email_b, subj, html_b)
            time.sleep(EMAIL_SLEEP_SECONDS) 
            # Mark emailed_at only after BOTH succeeded
        
            (
                supabase.table("matches")
                .update(
                    {
                        "emailed_at": now_iso,
                        # keep snapshot fields consistent too (optional but nice)
                        "user_low_name": low_name,
                        "user_high_name": high_name,
                        "compatibility_reasons": reasons_text,
                    }
                )
                .eq("round_id", round_id)
                .eq("user_low", low)
                .eq("user_high", high)
                .execute()
            )
        

            print(f"[email] ✅ sent + marked emailed_at: {email_a} <-> {email_b}")

        except Exception as e:
            print(f"[email] ❌ failed for pair {email_a} <-> {email_b}: {e}")
            # do NOT mark emailed_at

            # NOTE: Avoid running test emails at import time.
            # If you want a quick manual test, run this file directly and add your own
            # guarded code under the `if __name__ == "__main__":` block.


# In[23]:


def bump_next_match_drop_date(days: int = 4):
    """
    Reads globals row (id='global') from match_drop.match_drop_date and bumps it by `days`.
    Stores as ISO-8601 UTC string.
    """
    resp = (
        supabase.table("match_drop")
        .select("match_drop_date")
        .eq("id", "global")
        .single()
        .execute()
    )
    
    if not resp.data or not resp.data.get("match_drop_date"):
        raise RuntimeError("match_drop_date not found for id='global'")

    cur = resp.data["match_drop_date"]
    print(cur)
    # Supabase typically returns ISO string; parse robustly for 'Z'
    if isinstance(cur, str):
        cur_dt = datetime.fromisoformat(cur.replace("Z", "+00:00"))
    elif isinstance(cur, datetime):
        cur_dt = cur
    else:
        raise TypeError(f"Unexpected match_drop_date type: {type(cur)}")

    if cur_dt.tzinfo is None:
        cur_dt = cur_dt.replace(tzinfo=timezone.utc)

    new_dt = cur_dt + timedelta(days=days)
    new_iso = new_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    upd = (
        supabase.table("match_drop")
        .update({"match_drop_date": new_iso})
        .eq("id", "global")
        .execute()
    )
    return cur, new_iso, upd


ADMIN_EMAIL = "nin002@ucsd.edu"

def send_admin_notification(subject: str, body: str):
    """Fire-and-forget admin ping so you know a CI task finished."""
    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": RESEND_FROM,
                "to": [ADMIN_EMAIL],
                "subject": subject,
                "text": body,
            },
            timeout=20,
        )
        print(f"[admin] notification sent: {subject}")
    except Exception as e:
        print(f"[admin] notification failed (non-fatal): {e}")


# In[48]:


def main():
   
    X,users_ids,ids_to_info=get_X_ids_and_namemap()
    print(len(users_ids))
    banned_pairs = fetch_past_pairs(supabase)
    
    banned_pairs=list(banned_pairs)
    apply_ban_penalty_inplace(X, ids_to_info, banned_pairs)
    
    pref=get_preference_matrix(X)

    result = Find_all_Irving_partner(pref)

    res_pairs=all_matchings_to_ids(result[0], users_ids)
    
    check_match_results(res_pairs, ids_to_info)
    
   
    check_match_results(banned_pairs, ids_to_info) 
    
    round_id = datetime.now(timezone.utc).date().isoformat()  # e.g. "2026-01-03"
    
 
    send_matches_and_mark(res_pairs, ids_to_info, round_id)  
    old_dt, new_dt, _ = bump_next_match_drop_date(days=4)
    print(f"[match_drop] bumped match_drop_date: {old_dt} -> {new_dt}")

    send_admin_notification(
        subject=f"[Genuinely] ✅ main() done — round {round_id}",
        body=(
            f"main() completed successfully.\n"
            f"Round: {round_id}\n"
            f"Pairs matched: {len(res_pairs)}\n"
            f"Emails sent: {len(res_pairs) * 2}\n"
            f"Next match drop: {new_dt}"
        ),
    )
    
    
# In[54]:


import os, json, time, hmac, hashlib, base64
import requests


SITE_URL= "https://www.genuinely.life" #Use for deployment
#SITE_URL= "http://localhost:3000" #uncomment for testing on local host
SECRET=os.environ["FEEDBACK_SIGNING_SECRET"].encode("utf-8")

def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")

def sign_token(payload: dict) -> str:
    """
    payload example:
      { "match_id": "...", "rater_id": "...", "rating": "like", "exp": 1234567890 }
    """
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = b64url_encode(payload_json)

    sig = hmac.new(SECRET, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = b64url_encode(sig)

    return f"{payload_b64}.{sig_b64}"

def build_feedback_link(match_id: str, rater_id: str, rating: str, ttl_seconds: int = 7*24*3600) -> str:
    exp = int(time.time()) + ttl_seconds
    token = sign_token({
        "match_id": match_id,
        "rater_id": rater_id,
        "rating": rating,   # "like" or "dislike"
        "exp": exp,
    })
    return f"{SITE_URL}/api/feedback?token={token}"

def send_feedback_email(to_email: str, match_id: str, rater_id: str, match_name: str):
    like_url = build_feedback_link(match_id, rater_id, "like")
    dislike_url = build_feedback_link(match_id, rater_id, "dislike")

    subject = "Just Checking In "

    html = f"""
    <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;line-height:1.5;color:#111">

      <p style="margin:0 0 12px;color:#444">
        You were recently matched with <strong>{match_name}</strong>.
      </p>

      <p style="margin:0 0 16px;color:#444">
        Did this match feel like a good fit?
      </p>

      <div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0">
        <a href="{like_url}"
           style="text-decoration:none;padding:10px 16px;border-radius:6px;border:1px solid #ccc;color:#111;font-weight:600">
          Yes
        </a>
        <a href="{dislike_url}"
           style="text-decoration:none;padding:10px 16px;border-radius:6px;border:1px solid #ccc;color:#111;font-weight:600">
          No
        </a>
      </div>

      <p style="margin:16px 0 0;color:#666;font-size:13px">
        This helps us improve future matches.
      </p>

    </div>
    """

    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": RESEND_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html,
        },
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Resend failed {r.status_code}: {r.text}")
    return r.json()






def get_second_latest_round_id():
    resp = (
        supabase.table("matches")
        .select("round_id, created_at")
        .order("created_at", desc=True)
        .limit(200)  # increase if needed
        .execute()
    )

    rows = resp.data or []
    if len(rows) < 2:
        raise RuntimeError("Not enough matches found")

    latest_round = rows[0]["round_id"]

    for r in rows[1:]:
        if r["round_id"] != latest_round:
            return r["round_id"]

    raise RuntimeError(
        "Could not find a previous round_id in the fetched window. "
        "Increase the limit or check data."
    )




# In[ ]:





# In[28]:


def get_matches_for_round(round_id: str):
    resp = (
        supabase.table("matches")
        .select("id,user_low,user_high,round_id")
        .eq("round_id", round_id)
        .execute()
    )
    return resp.data or []


# In[29]:


profile_cache = {}
#make less api call because each use
def get_user_info(uid: str):
    if uid in profile_cache:
        return profile_cache[uid]

    resp = (
        supabase.table("profiles")
        .select("id,email,name")
        .eq("id", uid)
        .maybe_single()
        .execute()
    )
    if not resp.data:
        raise RuntimeError(f"Profile not found: {uid}")

    profile_cache[uid] = resp.data
    return resp.data

# Design decision: when to ask user for feedback.
# Originally followed up ~3 days after match; now sending ~5 days after match.
# In[30]:


def send_feedback_for_latest_round():
    round_id = get_second_latest_round_id() 
    print(f"[feedback] Latest round: {round_id}")

    matches = get_matches_for_round(round_id)
    print(f"[feedback] Found {len(matches)} matches")

    sent = 0
    for i, m in enumerate(matches, start=1):
        match_id = m["id"]
        user_a = m["user_low"]
        user_b = m["user_high"]

        prof_a = get_user_info(user_a)
        prof_b = get_user_info(user_b)

        # Email A about B
        send_feedback_email(
            to_email=prof_a["email"],
            match_id=match_id,
            rater_id=user_a,
            match_name=prof_b.get("name") or "your match",
        )
        sent += 1
        print(f"[feedback] ({sent}) sent to {prof_a['email']} for match {match_id}")
        time.sleep(EMAIL_SLEEP_SECONDS)

        # Email B about A
        send_feedback_email(
            to_email=prof_b["email"],
            match_id=match_id,
            rater_id=user_b,
            match_name=prof_a.get("name") or "your match",
        )
        sent += 1
        print(f"[feedback] ({sent}) sent to {prof_b['email']} for match {match_id}")
        time.sleep(EMAIL_SLEEP_SECONDS)

        print(f"[feedback] DONE. Sent {sent} emails for round {round_id}.")

    send_admin_notification(
        subject=f"[Genuinely] ✅ feedback done — round {round_id}",
        body=(
            f"send_feedback_for_latest_round() completed successfully.\n"
            f"Round: {round_id}\n"
            f"Feedback emails sent: {sent}"
        ),
    )

# Update terms and service or inform all users

# In[31]:


def send_email_resend_plain_text(
    to_email: str,
    subject: str,
    text: str,
):
    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": RESEND_FROM,          # e.g. "Genuinely <contact@send.genuinely.life>"
            "to": [to_email],
            "subject": subject,
            "text": text,                # ✅ plain text (best for spam)
            "reply_to": "contact@send.genuinely.life",
        },
        timeout=20,
    )

    if r.status_code >= 300:
        raise RuntimeError(f"Resend error {r.status_code}: {r.text}")

    return r.json()


# In[32]:





# In[33]:


def get_users_missing_terms_agreement() -> List[str]:
    """
    Returns a list of user emails who have not agreed to Terms of Service.
    """
    resp = (
        supabase
        .table("profiles")
        .select("email")
        .eq("active", True)
        .eq("agreed_to_terms", False)
        .execute()
    )
   

    if not resp.data:
        return []

    # Filter defensively
    emails = [
        row["email"]
        for row in resp.data
        if row.get("email")
    ]

    return emails


# In[34]:


def notify_users_about_terms():
    emails = get_users_missing_terms_agreement()
    EMAIL_SUBJECT = "Update regarding future Genuinely matches"

    EMAIL_TEXT = """Hi,

    As Genuinely has grown and more UCSD students enjoy using it to meet new people and make friends, we added Terms of Service to clearly explain how the project works and what to expect when using it. To keep receiving new match emails from Genuinely, please log in and agree to the Terms of Service on your dashboard:

    https://www.genuinely.life/

    If you don’t take any action, that’s completely okay — you’ll simply be opted out of receiving future matches until you agree to the Terms. Agreeing to the Terms helps Genuinely continue operating responsibly as the project grows. It ensures everyone has a shared understanding of how matching works, personal safety expectations, and what the platform can and can’t provide.
    For those who are curious, the Terms of Service cover things like:

    •	What Genuinely does (and doesn’t do).
    •	Safety and personal responsibility when meeting others.
    •	Clarifying that Genuinely is a student-led project, not affiliated with UCSD.

    If you have any questions, feel free to reach out at contact@send.genuinely.life.
    Thanks for being part of Genuinely’s mission to help UCSD students connect.

    Nick,
    Genuinely

    You’re receiving this because you’re an active Genuinely user.
    To stop receiving emails, log in and pause matching.

    """
    print(f"Sending terms update to {len(emails)} users")

    for email in emails:
        try:
            send_email_resend_plain_text(
                to_email=email,
                subject=EMAIL_SUBJECT,
                text=EMAIL_TEXT,
            )
            time.sleep(EMAIL_SLEEP_SECONDS)  # ✅ critical for deliverability
        except Exception as e:
            print(f"Failed to send to {email}: {e}")



# In[36]:


def get_active_user_emails() -> List[str]:
    
    resp = (
        supabase
        .table("profiles")
        .select("email")
        .eq("active",True)
        .eq("agreed_to_terms", True)
        .execute()
    )
   

    if not resp.data:
        return []

    # Filter defensively
    emails = [
        row["email"]
        for row in resp.data
        if row.get("email")
    ]
    
    return emails


# In[45]:


def get_inactive_user_emails() -> List[str]:
    
    resp = (
        supabase
        .table("profiles")
        .select("email")
        .eq("active",False)
        .execute()
    )
   

    if not resp.data:
        return []

    # Filter defensively
    emails = [
        row["email"]
        for row in resp.data
        if row.get("email")
    ]
    
    return emails


# In[37]:


def send_promo():
    subject = "Meet-up location (Froyo)"

    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.4;">
      <p>
        If you’re planning to meet your match soon, here’s a possible
        meet-up location.
      </p>
    
      <img
        src="https://www.genuinely.life/discounts/Froyo.png"
        alt="Meet-up location information"
        width="600"
        style="display:block;width:100%;max-width:600px;height:auto;margin:0 auto;border-radius:12px;"
      />
    
      <p style="margin-top:12px;">
        If the image doesn’t load, you can view it here:
        <a href="https://www.genuinely.life/discounts/tapex">View details</a>
        <br /><br />
        You’re receiving this because you’re an active Genuinely user.
        To stop receiving emails, log in and pause matching.
      </p>
    </div>
    """.strip()
    emails = get_active_user_emails()
  
    for email in emails:
        try:
            send_email_resend(
                to_email=email,
                subject=subject,
                html=html,
            )
            time.sleep(EMAIL_SLEEP_SECONDS)  # ✅ critical for deliverability
        except Exception as e:
            print(f"Failed to send to {email}: {e}")
    print(f"[promo] sent to {len(emails)} users")






