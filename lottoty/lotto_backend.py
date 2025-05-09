from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import json
import os
import random
from collections import defaultdict, Counter
from math import comb

app = FastAPI(
    title="Mega Lotto API",
    description="Backend for lottery number tracking and analysis",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_spin_results = {
    "numbers": [],
    "frequencies": {},
    "generation_time": None,
    "source": "uninitialized",
    "lucky_pool_frequencies": {}  
}

# Data storage configuration
DATA_DIR = "data"
RECENT_COMBINATIONS_FILE = "recent_combinations.json"
FREQUENCY_FILE = "number_frequencies.json"
MAX_RECENT = 10  # Maximum recent combinations to store
LUCKY_NUMBERS_POOL = []
LUCKY_NUMBERS_FREQUENCIES = Counter()
LUCKY_NUMBERS_FILE = "lucky_numbers.json"

class Draw(BaseModel):
    numbers: List[int]
    draw_date: str = None

os.makedirs(DATA_DIR, exist_ok=True)
recent_combinations = []
number_frequencies = defaultdict(int)

def generate_representative_sample(sample_size=1000):
    """Generate representative sample of combinations"""
    sample = set()
    while len(sample) < sample_size:
        combo = tuple(sorted(random.sample(range(1, 46), 6)))
        sample.add(combo)
    return list(sample)

def initialize_lucky_numbers():
    """Initialize the lucky numbers pool"""
    global LUCKY_NUMBERS_POOL, LUCKY_NUMBERS_FREQUENCIES
    
    try:
        LUCKY_NUMBERS_POOL = generate_representative_sample(1000)
        
        flat_numbers = [num for combo in LUCKY_NUMBERS_POOL for num in combo]
        LUCKY_NUMBERS_FREQUENCIES = Counter(flat_numbers)
        
    except Exception as e:
        print(f"Error initializing lucky numbers: {e}")
        LUCKY_NUMBERS_POOL = []
        LUCKY_NUMBERS_FREQUENCIES = Counter()
        raise
            
def generate_new_lucky_pool():
    """Generate a fresh lucky numbers pool and save it"""
    global LUCKY_NUMBERS_POOL, LUCKY_NUMBERS_FREQUENCIES
    
    print("Generating new lucky numbers pool...")
    LUCKY_NUMBERS_POOL = generate_representative_sample(sample_size=1000)
    
    # Calculate frequencies
    flat_numbers = [num for combo in LUCKY_NUMBERS_POOL for num in combo]
    LUCKY_NUMBERS_FREQUENCIES = Counter(flat_numbers)
    
    # Save to file
    save_lucky_numbers()

def save_lucky_numbers():
    """Save the lucky numbers pool to file"""
    try:
        data = {
            "pool": [list(combo) for combo in LUCKY_NUMBERS_POOL],
            "frequencies": dict(LUCKY_NUMBERS_FREQUENCIES)
        }
        with open(f"{DATA_DIR}/{LUCKY_NUMBERS_FILE}", "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving lucky numbers: {e}")

# Update your load_data() function to include lucky numbers initialization
def load_data():
    """Load all data from storage files"""
    global recent_combinations, number_frequencies
    
    initialize_lucky_numbers()

def save_data():
    """Save all data to storage files"""
    with open(f"{DATA_DIR}/{RECENT_COMBINATIONS_FILE}", "w") as f:
        json.dump(recent_combinations[-MAX_RECENT:], f)
    
    # Save frequency data
    with open(f"{DATA_DIR}/{FREQUENCY_FILE}", "w") as f:
        json.dump(dict(number_frequencies), f)

load_data()

@app.get("/", tags=["Root"], summary="API Information")
async def root():
    """Display welcome message and available endpoints"""
    return {
        "message": "Welcome to Mega Lotto API",
        "endpoints": {
            "record": "/record/ (POST) - Submit new lottery numbers",
            "recent": "/recent/ (GET) - Get recent combinations",
            "frequency": "/frequency/ (GET) - Get number frequencies",
            "generate": "/generate/ (GET) - Generate random numbers",
            "lucky_numbers": "/lucky_numbers/ (GET) - Get lucky numbers based on frequency analysis"
        }
    }


@app.post("/record/", status_code=201)
async def record_combination(draw: Draw):
    """Record a new lottery combination and update frequencies"""
    if len(draw.numbers) != 6:
        raise HTTPException(status_code=400, detail="Exactly 6 numbers required")
    
    if any(n < 1 or n > 45 for n in draw.numbers):
        raise HTTPException(status_code=400, detail="Numbers must be between 1 and 45")
    
    if not draw.draw_date:
        draw.draw_date = datetime.now().isoformat()
    
    recent_combinations.append({
        "numbers": draw.numbers,
        "draw_date": draw.draw_date
    })
    
    for number in draw.numbers:
        number_frequencies[number] += 1
    
    if len(recent_combinations) > MAX_RECENT:
        recent_combinations.pop(0)
    
    save_data()
    
    return {"message": "Combination recorded successfully"}

@app.get("/recent/", response_model=List[Dict])
async def get_recent_combinations():
    """Get recent combinations (max 10)"""
    return recent_combinations[-MAX_RECENT:]

@app.get("/frequency/", response_model=Dict[int, int])
async def get_frequencies():
    # Ensure we return all numbers 1-45, even those with 0 counts
    full_frequencies = {num: number_frequencies.get(num, 0) for num in range(1, 46)}

    return full_frequencies

def save_current_state():
    """Save current results to disk"""
    with open(f"{DATA_DIR}/current_results.json", "w") as f:
        json.dump(current_spin_results, f)

@app.get("/biased_spin/")
async def biased_spin():
    try:
        if not LUCKY_NUMBERS_POOL:
            initialize_lucky_numbers()
        
        # 1. Get the ACTUAL frequency distribution we'll use
        full_frequencies = dict(LUCKY_NUMBERS_FREQUENCIES)
        
        # 2. Create weighted pool based on exact frequencies
        weighted_pool = []
        for num, freq in full_frequencies.items():
            weighted_pool.extend([num] * freq)
        
        # 3. Draw numbers ensuring they match the frequencies
        spin_result = []
        attempts = 0
        max_attempts = 100
        
        while len(spin_result) < 6 and attempts < max_attempts:
            num = random.choice(weighted_pool)
            if num not in spin_result:
                spin_result.append(num)
            attempts += 1
        
        if len(spin_result) < 6:
            # Fallback if we can't get unique numbers
            spin_result.extend(random.sample(
                [n for n in range(1, 46) if n not in spin_result],
                6 - len(spin_result)
            ))
        
        # 4. Update state with EXACT frequencies
        update_global_state(
            numbers=spin_result,
            frequencies={num: full_frequencies[num] for num in spin_result},
            full_frequencies=full_frequencies,
            source="lucky_pool"
        )
        
        return current_spin_results
        
    except Exception as e:
        raise HTTPException(500, detail=f"Spin failed: {str(e)}")
    
def update_global_state(numbers, frequencies, full_frequencies, source):
    global current_spin_results
    current_spin_results = {
        "numbers": sorted(numbers),
        "frequencies": {num: full_frequencies[num] for num in numbers},  # Ensure exact match
        "generation_time": datetime.now().isoformat(),
        "source": source,
        "lucky_pool_frequencies": full_frequencies  # Store complete frequency data
    }
    save_current_state()

@app.get("/lucky_frequencies/")
async def get_lucky_frequencies():
    try:
        if not LUCKY_NUMBERS_POOL:
            generate_new_lucky_pool()
        
        # Return all numbers 1-45 with their frequencies
        full_frequencies = {num: LUCKY_NUMBERS_FREQUENCIES.get(num, 0) for num in range(1, 46)}
        return full_frequencies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lucky frequencies: {str(e)}")

@app.get("/refresh_lucky_numbers/")
async def refresh_lucky_numbers():
    try:
        generate_new_lucky_pool()
        return {"message": "Lucky numbers pool refreshed successfully",
                "pool_size": len(LUCKY_NUMBERS_POOL),
                "total_combinations": comb(45, 6)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh lucky numbers: {str(e)}")

@app.get("/current_frequencies/")
async def get_current_frequencies():
    if not current_spin_results["numbers"]:
        raise HTTPException(status_code=404, detail="No spin results available")
    
    return {
        "numbers": current_spin_results["numbers"],
        "frequencies": current_spin_results["frequencies"],
        "top_historical": sorted(
            number_frequencies.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:6]
    }

@app.get("/reset/") 
async def reset_data(reset_frequencies: bool = True, reset_recent: bool = True):
    """Reset stored JSON data"""
    global recent_combinations, number_frequencies

    if reset_recent:
        recent_combinations = []
        with open(f"{DATA_DIR}/{RECENT_COMBINATIONS_FILE}", "w") as f:
            json.dump([], f)

    if reset_frequencies:
        number_frequencies = defaultdict(int)
        with open(f"{DATA_DIR}/{FREQUENCY_FILE}", "w") as f:
            json.dump({}, f)

    return {"message": "Data reset successfully"}

@app.get("/generate/")
async def generate_numbers():
    numbers = sorted(random.sample(range(1, 46), 6))
    return {"numbers": numbers}

@app.get("/lucky_numbers/")
async def lucky_numbers():
    try:
        if not current_spin_results["numbers"]:
            return await biased_spin()
            
        valid_numbers = all(
            current_spin_results["frequencies"][num] == 
            current_spin_results["lucky_pool_frequencies"].get(num, 0)
            for num in current_spin_results["numbers"]
        )
        
        if not valid_numbers:
            return await biased_spin()
            
        return current_spin_results
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    
@app.get("/verify_frequencies/")
async def verify_frequencies():
    if not current_spin_results["numbers"]:
        raise HTTPException(404, "No spin results available")
    
    mismatches = [
        num for num in current_spin_results["numbers"]
        if current_spin_results["frequencies"][num] != 
           current_spin_results["lucky_pool_frequencies"].get(num, 0)
    ]
    
    return {
        "is_valid": len(mismatches) == 0,
        "mismatched_numbers": mismatches,
        "current_numbers": current_spin_results["numbers"],
        "displayed_frequencies": current_spin_results["frequencies"],
        "actual_frequencies": {
            num: current_spin_results["lucky_pool_frequencies"].get(num, 0)
            for num in current_spin_results["numbers"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
