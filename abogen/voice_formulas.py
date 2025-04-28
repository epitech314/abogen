from constants import VOICES_INTERNAL

# Calls parsing and loads the voice to gpu or cpu
def get_new_voice(pipeline, formula, use_gpu):
    try:
        weighted_voice = parse_voice_formula(pipeline, formula)            
        device = "cuda" if use_gpu else "cpu"
        return weighted_voice.to(device)
    except Exception as e:
        raise ValueError(f"Failed to create voice: {str(e)}")
    
# Parse the formula and get the combined voice tensor        
def parse_voice_formula(pipeline, formula):
    """Parse the voice formula string and return the combined voice tensor."""
    if not formula.strip():
        raise ValueError("Empty voice formula")
        
    # Initialize the weighted sum
    weighted_sum = None
    
    # Split the formula into terms
    terms = formula.split('+')
    
    for term in terms:
        # Parse each term (format: "0.333 * voice_name")
        weight, voice_name = term.strip().split('*')
        weight = float(weight.strip())
        voice_name = voice_name.strip()
        
        # Get the voice tensor
        # use VOICES_INTERNAL
        if voice_name not in VOICES_INTERNAL:
            raise ValueError(f"Unknown voice: {voice_name}")
            
        voice_tensor = pipeline.load_single_voice(voice_name)
        
        # Add to weighted sum
        if weighted_sum is None:
            weighted_sum = weight * voice_tensor
        else:
            weighted_sum += weight * voice_tensor
            
    return weighted_sum