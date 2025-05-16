from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import json
import os
import random
from collections import defaultdict, Counter
from math import comb

# Create FastAPI app with metadata
app = FastAPI(
    title="Mega Lotto API",
    description="Backend for lottery number tracking and analysis",
    version="1.0.0"
)

# Allow all cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data directory and filenames
DATA_DIR = "data"
RECENT_COMBINATIONS_FILE = "recent_combinations.json"
LUCKY_NUMBERS_FILE = "lucky_numbers.json"
CONFIG_FILE = "config.json"
MAX_RECENT = 10  # Limit for recent draws

# Storage for lucky numbers pool and frequencies
LUCKY_NUMBERS_POOL = []
SAMPLE_SIZE = 1000
LUCKY_NUMBERS_FREQUENCIES = Counter()

# Create the data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Pydantic model for submitted draw data
class Draw(BaseModel):
    numbers: List[int]
    draw_date: str = None


class ConfigUpdate(BaseModel):
    sample_size: Optional[int] = None


# In-memory data for recent draws and number frequencies
recent_combinations = []
number_frequencies = defaultdict(int)

# ------------------------------------------------------
# Main logic
def generate_representative_sample(sample_size: int):
    sample = set()
    max_possible = comb(45, 6)  # Total possible 6-number combinations from 1-45
    
    # Ensure sample size doesn't exceed maximum possible combinations
    sample_size = min(sample_size, max_possible)
    
    while len(sample) < sample_size:
        combo = tuple(sorted(random.sample(range(1, 46), 6)))
        sample.add(combo)
    return list(sample)
# Initialize the lucky numbers pool with random combinations and calculate their frequencies
def initialize_lucky_numbers():
    """Initialize or reinitialize the lucky numbers pool"""
    global LUCKY_NUMBERS_POOL, LUCKY_NUMBERS_FREQUENCIES, SAMPLE_SIZE
    try:
        # Try to load config if exists
        if os.path.exists(f"{DATA_DIR}/{CONFIG_FILE}"):
            with open(f"{DATA_DIR}/{CONFIG_FILE}", "r") as f:
                config = json.load(f)
                SAMPLE_SIZE = config.get("sample_size", 1000)
        
        LUCKY_NUMBERS_POOL = generate_representative_sample(SAMPLE_SIZE)
        flat_numbers = [num for combo in LUCKY_NUMBERS_POOL for num in combo]
        LUCKY_NUMBERS_FREQUENCIES = Counter(flat_numbers)
    except Exception as e:
        print(f"Error initializing lucky numbers: {e}")
        LUCKY_NUMBERS_POOL = []
        LUCKY_NUMBERS_FREQUENCIES = Counter()
        raise

# Generate a new pool and save to file
def generate_new_lucky_pool(sample_size: int = None):
    """Generate a new pool with customizable sample size"""
    global LUCKY_NUMBERS_POOL, LUCKY_NUMBERS_FREQUENCIES, SAMPLE_SIZE
    
    if sample_size is not None:
        SAMPLE_SIZE = sample_size
        # Save the new sample size to config
        with open(f"{DATA_DIR}/{CONFIG_FILE}", "w") as f:
            json.dump({"sample_size": SAMPLE_SIZE}, f)
    
    print(f"Generating new lucky numbers pool with sample size {SAMPLE_SIZE}...")
    LUCKY_NUMBERS_POOL = generate_representative_sample(SAMPLE_SIZE)
    flat_numbers = [num for combo in LUCKY_NUMBERS_POOL for num in combo]
    LUCKY_NUMBERS_FREQUENCIES = Counter(flat_numbers)
    save_lucky_numbers()

def save_lucky_numbers():
    """Save lucky pool and frequencies to JSON"""
    try:
        data = {
            "pool": [list(combo) for combo in LUCKY_NUMBERS_POOL],
            "frequencies": dict(LUCKY_NUMBERS_FREQUENCIES),
            "sample_size": SAMPLE_SIZE
        }
        with open(f"{DATA_DIR}/{LUCKY_NUMBERS_FILE}", "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving lucky numbers: {e}")

# Load necessary data (currently only initializes lucky pool)
def load_data():
    global recent_combinations, number_frequencies
    initialize_lucky_numbers()

# Load data on startup
load_data()

# Save recent draws
def save_data():
    with open(f"{DATA_DIR}/{RECENT_COMBINATIONS_FILE}", "w") as f:
        json.dump(recent_combinations[-MAX_RECENT:], f)

# ------------------------------------------------------
# API Routes

@app.get("/", tags=["Root"], summary="API Information")
async def root():
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

@app.post("/config/", status_code=200)
async def update_config(config: ConfigUpdate):
    """Update configuration including sample size"""
    if config.sample_size is not None:
        if config.sample_size < 1:
            raise HTTPException(status_code=400, detail="Sample size must be at least 1")
        generate_new_lucky_pool(config.sample_size)
    return {"message": "Configuration updated successfully", "sample_size": SAMPLE_SIZE}

@app.get("/config/", status_code=200)
async def get_config():
    """Get current configuration"""
    return {"sample_size": SAMPLE_SIZE}

@app.get("/pool_info/", status_code=200)
async def get_pool_info():
    """Get information about the current lucky numbers pool"""
    return {
        "pool_size": len(LUCKY_NUMBERS_POOL),
        "sample_size": SAMPLE_SIZE,
        "number_frequencies": dict(LUCKY_NUMBERS_FREQUENCIES)
    }

# Record a new lottery draw
@app.post("/record/", status_code=201)
async def record_combination(draw: Draw):
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

# Get up to 10 recent combinations
@app.get("/recent/", response_model=List[Dict])
async def get_recent_combinations():
    return recent_combinations[-MAX_RECENT:]

# Save current spin result to JSON
def save_current_state():
    with open(f"{DATA_DIR}/current_results.json", "w") as f:
        json.dump(current_spin_results, f)

# Fetch the lucky numbers with the highest appearances
@app.get("/biased_spin/")
async def biased_spin():
    try:
        if not LUCKY_NUMBERS_POOL:
            initialize_lucky_numbers()
        
        # Create weighted pool from lucky frequencies
        weighted_pool = []
        for num, freq in LUCKY_NUMBERS_FREQUENCIES.items():
            weighted_pool.extend([num] * freq)

        spin_result = []
        attempts = 0
        while len(spin_result) < 6 and attempts < 100:
            num = random.choice(weighted_pool)
            if num not in spin_result:
                spin_result.append(num)
            attempts += 1

        if len(spin_result) < 6:
            spin_result.extend(random.sample(
                [n for n in range(1, 46) if n not in spin_result],
                6 - len(spin_result)
            ))

        update_global_state(
            numbers=spin_result,
            frequencies={num: LUCKY_NUMBERS_FREQUENCIES[num] for num in spin_result},
            full_frequencies=dict(LUCKY_NUMBERS_FREQUENCIES),
            source="lucky_pool"
        )
        return current_spin_results

    except Exception as e:
        raise HTTPException(500, detail=f"Spin failed: {str(e)}")

# Update global spin result and save
def update_global_state(numbers, frequencies, full_frequencies, source):
    global current_spin_results
    current_spin_results = {
        "numbers": sorted(numbers),
        "frequencies": frequencies,
        "generation_time": datetime.now().isoformat(),
        "source": source,
        "lucky_pool_frequencies": full_frequencies
    }
    save_current_state()

# Reset recent combinations http://127.0.0.1:8000/reset/?reset_recent=true
@app.get("/reset/")
async def reset_data(reset_recent: bool = True):
    global recent_combinations

    if reset_recent:
        recent_combinations = []
        with open(f"{DATA_DIR}/{RECENT_COMBINATIONS_FILE}", "w") as f:
            json.dump([], f)

    return {"message": "Data reset successfully"}

# Get cached lucky spin or perform new one
@app.get("/lucky_numbers/")
async def lucky_numbers():
    try:
        if not current_spin_results["numbers"]:
            return await biased_spin()

        # Validate current results match stored lucky frequencies
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
