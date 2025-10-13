import json
import base64
import os
import google.generativeai as genai
import vertexai
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any


class AudioAnalysisPipeline:
    """
    Complete 6-step pipeline for Hindi audio transcription, evaluation, analysis,
    comparison, and final consolidated output generation.
    """
    
    def __init__(self, credentials_path: str, project_id: str = None, location: str = "us-central1"):
        """
        Initialize the pipeline with credentials
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file (Gemini API key)
            project_id: Google Cloud project ID
            location: Google Cloud location
        """
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.project_id = project_id if project_id else str(os.environ.get("GOOGLE_CLOUD_PROJECT"))
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        self.model_lite = genai.GenerativeModel("gemini-2.5-flash")
        self.model_pro = genai.GenerativeModel("gemini-2.5-pro")
        self.generation_config = genai.GenerationConfig(temperature=0.1)
        
        # Initialize all prompts
        self.transcription_prompt = ''' This is a Hindi language conversation happens between a caller from the govt organisation and a tribal people . U need to pay close attention to the conversation and generate the transcript of it . Also make sure to do the speaker diarization. Donot pay much attention to the background noise and try not to include it in the transcript. Output it in the below mentioned json format .
If a speaker cannot be identified, label them as "Unknown."
Context about the caller and conversation - The conversation is all about the a speaker  asking  citizens about to whom they want to see as their next cheif minister and to whom they want to see as their next local leader. The speaker will give them multiple options of leader name as well as their party and the citizen have to choose between them. It is just for information purpose and not for actual casting of vote. The speaker may ask the vidhansabha constituency details and the mobile number and the religion of the citizen .The speaker may ask question about wheather they are satisfied by the work of the current leader or chief minister etc. and take opinion of the people.
OUTPUT THE EXACT NUMBER OF SPEAKER.DONOT BIASED BY THE CONTEXT. ANALYSE THE AUDIO PROPERLY .
Provide the output in the following JSON structure:
{
  "Call Details": {
    "Number of Speakers": "<total_number_of_speakers>",
    "Transcript": [
      {
        "Speaker": "<Speaker>",
        "Timestamp": {
          "Start": "<start_time>",
          "End": "<end_time>"
        },
        "Voice": "<extracted_text_from_audio>"
      },
      {
        "Speaker": "<Speaker>",
        "Timestamp": {
          "Start": "<start_time>",
          "End": "<end_time>"
        },
        "Voice": "<extracted_text_from_audio>"
      },
      ...
    ]
  }
} '''
        
        self.evaluation_prompt = ''' You are an expert quality analyst tasked with evaluating whether a survey agent properly asked all required questions during a Hindi language audio call. Your job is to analyze the provided transcript and determine if each survey question was asked correctly by the agent.

## CRITICAL INSTRUCTIONS:

1. **IDENTIFY THE AGENT**: First, determine which speaker in the transcript is the survey agent (the person asking questions) and which is the respondent (the person answering)
   - The agent will be asking questions from the survey
   - The respondent will be providing answers
   - Usually, the agent speaks first and asks multiple questions

2. **ANALYZE EACH QUESTION**: For each of the 17 survey questions listed below, you must determine:
   - **"asked properly"** - The agent asked the question with the exact or very similar wording, covering all key elements
   - **"asked"** - The agent asked the question but with modified/shortened wording, or the essence of the question was asked
   - **"not asked"** - The agent did not ask this question at all in the transcript

3. **HINDI LANGUAGE UNDERSTANDING**:
   - Understand variations and synonyms in Hindi
   - The agent may use slightly different words but same meaning
   - Consider conversational Hindi variations (e.g., "आपकी उम्र क्या है?" vs "उम्र कितनी है?")
   - Account for informal language and regional dialects

4. **ASSESSMENT CRITERIA**:
   - **"asked properly"**: The question matches 80-100% with the original wording, all key components are present
   - **"asked"**: The question captures the core intent but wording is significantly different (50-80% match), or question is incomplete/rushed
   - **"not asked"**: The question is completely missing from the conversation (0-50% match)

5. **SEQUENTIAL ANALYSIS**: Go through the transcript chronologically and map each agent's question to the survey questions

6. **CONTEXT MATTERS**: Sometimes questions are asked indirectly or as part of another conversation. Use context to determine if the information was sought.

## SURVEY QUESTIONS TO EVALUATE:

### Section 1 – Personal Questions



**Question 1:** क्या मैं आपकी उम्र जान सकता हूँ ?

**Question 2:** लिंग: (पूछना नहीं है देखकर भरें)
**Note:** This is an observational question. Mark as "not asked" since it's not meant to be asked.

**Question 3:** आप क्या काम करते हैं ?

**Question 4:** आप कौन से धर्म से हैं?

**Question 5:** आपकी जाति क्या है ?

---

### Section 2 – Political Questions

**Question 6:** आपके एमएलए/ विधायक का क्या नाम है?

**Question 7:** क्या आप अपने विधायक के काम से खुश हैं ?

**Question 8:** आप अगले विधायक के रूप में किसे देखना चाहते हैं ?



**Question 9:** आप आने वाले विधानसभा चुनाव में किस पार्टी को वोट देंगे?

**Question 10:** 2020 के पिछले विधानसभा चुनाव में आपने किस पार्टी को वोट दिया था?

**Question 11:** क्या आप बिहार सरकार द्वारा 2020 – 25 में किए गए काम से शंतुष्ट हैं ?

**Question 12:** आप अगले मुख्यमंत्री के रूप में किसे देखना चाहते हैं ?

---

### Section 3 – Observational Questions

**Question 13:** आप गाँव में रहते हैं या शहर में?

**Question 14:** ब्लाक का नाम (आप जहाँ है उस ब्लाक का नाम चुनें)

**Question 15:** गाँव / पंचायत का नाम (आप जिस गाँव/ पंचायत में है उस पंचायत का नाम चुनें)

**Question 16:** सर क्या मैं आपका मोबाइल नंबर जान सकता हूँ ?

---

## EVALUATION EXAMPLES FOR CLARITY:

**Example 1 - Question 2 (Age):**
- Original: "क्या मैं आपकी उम्र जान सकता हूँ ?"
- Agent says: "क्या मैं आपकी उम्र जान सकता हूँ?" → **"asked properly"**
- Agent says: "आपकी उम्र क्या है?" → **"asked properly"**
- Agent says: "उम्र कितनी है?" → **"asked"**
- Agent says: "कितने साल के हैं आप?" → **"asked"**
- Agent doesn't mention age at all → **"not asked"**

**Example 2 - Question 4 (Occupation):**
- Original: "आप क्या काम करते हैं ?"
- Agent says: "आप क्या काम करते हैं?" → **"asked properly"**
- Agent says: "आपका काम क्या है?" → **"asked properly"**
- Agent says: "क्या करते हैं आप?" → **"asked"**
- Agent says: "पेशा क्या है?" → **"asked"**
- Agent doesn't ask about occupation → **"not asked"**

**Example 3 - Question 10 (Voting intention):**
- Original: "आप आने वाले विधानसभा चुनाव में किस पार्टी को वोट देंगे?"
- Agent says: "आप आने वाले विधानसभा चुनाव में किस पार्टी को वोट देंगे?" → **"asked properly"**
- Agent says: "अगले चुनाव में किसको वोट देंगे?" → **"asked"**
- Agent says: "किस पार्टी को वोट देंगे?" (without mentioning upcoming election) → **"asked"**
- Agent doesn't ask about voting preference → **"not asked"**

## SPECIAL CONSIDERATIONS:

1. **Question 3 (Gender)**: This is observational and should NOT be asked. Always mark as "not asked" (this is correct behavior).



3. **Questions 15-16**: These ask for specific information (block name, village name, mobile number). The agent must specifically request this information.

4. **Implicit vs Explicit**: If the respondent volunteers information without being asked, mark the question as "not asked" unless the agent explicitly requested it.

5. **Conversational Flow**: Sometimes agents combine questions or ask them in a different order. This is acceptable as long as each question is asked.

## OUTPUT FORMAT:

Return your assessment in the following JSON structure with ONLY these three values: "asked properly", "asked", or "not asked"

{

  "quality_assessment": {
    "question_1": "asked properly / asked / not asked",
    "question_2": "asked properly / asked / not asked",
    "question_3": "asked properly / asked / not asked",
    "question_4": "asked properly / asked / not asked",
    "question_5": "asked properly / asked / not asked",
    "question_6": "asked properly / asked / not asked",
    "question_7": "asked properly / asked / not asked",
    "question_8": "asked properly / asked / not asked",
    "question_9": "asked properly / asked / not asked",
    
    "question_10": "asked properly / asked / not asked",
    "question_11": "asked properly / asked / not asked",
    "question_12": "asked properly / asked / not asked",
    "question_13": "asked properly / asked / not asked",
    "question_14": "asked properly / asked / not asked",
    "question_15": "asked properly / asked / not asked",
    "question_16": "asked properly / asked / not asked",
    
  },
  "summary": {
    "total_questions": 16,
    "asked_properly": 0,
    "asked": 0,
    "not_asked": 0
  }
}

## ANALYSIS WORKFLOW:

1. **Step 1**: Read the entire transcript carefully
2. **Step 2**: Identify which speaker is the agent and which is the respondent
3. **Step 3**: Go through each of the 16 survey questions one by one
4. **Step 4**: For each question, search the transcript for where the agent asked it
5. **Step 5**: Evaluate the quality: "asked properly", "asked", or "not asked"
6. **Step 6**: Provide the summary counts
7. **Step 7**: Return valid JSON output

## IMPORTANT REMINDERS:

- **BE THOROUGH**: Read every line of the transcript
- **UNDERSTAND HINDI NUANCES**: Recognize different ways to ask the same question
- **BE FAIR**: Don't penalize minor variations in wording
- **BE STRICT**: "asked properly" should only be used when the question is very close to the original
- **BE ACCURATE**: Double-check your assessment before finalizing
- **VALID JSON ONLY**: Ensure proper formatting with correct quotes and commas
- **USE EXACT VALUES**: Only use "asked properly", "asked", or "not asked" - no other values

Now, please analyze the Hindi transcript and provide the quality assessment in the specified JSON format:
 '''
        
        self.analysis_prompt = ''' You are an expert analyst tasked with extracting specific information from Hindi language audio call transcripts. Your job is to carefully analyze the provided transcript and extract answers to predefined survey questions.

## CRITICAL INSTRUCTIONS:

1. **READ THE ENTIRE TRANSCRIPT CAREFULLY** before answering any question
2. **EXTRACT ANSWERS ONLY FROM THE TRANSCRIPT** - Do not make assumptions or infer answers
3. **MATCH ANSWERS TO PROVIDED OPTIONS** - You must select from the given options only
4. **LANGUAGE HANDLING**: The transcript is in Hindi. Understand the context and meaning in Hindi to match with the provided options
5. **HANDLE MISSING INFORMATION**: If an answer to a question is not found in the transcript, output "Not Available"
6. **BE PRECISE**: Match the respondent's answer to the closest provided option based on the meaning and context
7. **OUTPUT FORMAT**: Return responses in valid JSON format only

## SURVEY QUESTIONS WITH OPTIONS:

### Section 1 – Personal Questions



**Question 1:** क्या मैं आपकी उम्र जान सकता हूँ ?
**Options:**
- 18-30 वर्ष
- 31-45 वर्ष
- 46-60 वर्ष
- 60 वर्ष से अधिक
- बताना नहीं चाहते

**Question 2:** लिंग: (पूछना नहीं है देखकर भरें)
**Options:**
- पुरुष
- महिला

**Question 3:** आप क्या काम करते हैं ?
**Options:**
- कृषि
- मजदूरी/दैनिक वेतन
- सरकारी नौकरी
- निजी नौकरी
- स्वरोजगार/व्यवसाय
- बेरोजगार
- हाउसवाइफ / गृहिणी
- छात्र / पढाई
- अन्य (कृपया उल्लेख करें)

**Question 4:** आप कौन से धर्म से हैं?
**Options:**
- हिन्दू
- मुस्लिम
- सिख
- क्रिस्चियन
- जैन
- बुद्धिस्ट
- किसी धर्म को नहीं मानता
- बताना नहीं चाहते

**Question 5:** आपकी जाति क्या है ?
**Options:**
- (विधानसभा के टॉप 12 जातियों की लिस्ट के अनुसार)

---

### Section 2 – Political Questions

**Question 6:** आपके एमएलए/ विधायक का क्या नाम है?
**Options:**
- MLA का नाम सही बताया
- MLA का नाम नहीं पता
- MLA का नाम गलत बताया

**Question 7:** क्या आप अपने विधायक के काम से खुश हैं ?
**Options:**
- हाँ
- नहीं
- कुछ कह नहीं सकते



**Question 8:** आप अगले विधायक के रूप में किसे देखना चाहते हैं ?
**Options:**
- (संभावित उम्मीदवारों की सुची के अनुसार)

**Question 9:** आप आने वाले विधानसभा चुनाव में किस पार्टी को वोट देंगे?
**Options:**
- JDU | NDA
- महागठबंधन | MGB
- जन सुराज पार्टी
- अन्य
- बीएसपि | BSP
- NOTA
- कह नहीं सकते

**Question 10:** 2020 के पिछले विधानसभा चुनाव में आपने किस पार्टी को वोट दिया था?
**Options:**
- JDU | NDA
- महागठबंधन | MGB
- लोक जनशक्ति पार्टी (लोजपा)
- अन्य
- बीएसपि | BSP
- NOTA
- कह नहीं सकते / याद नहीं
- वोट नहीं दिया

**Question 11:** क्या आप बिहार सरकार द्वारा 2020 – 25 में किए गए काम से शंतुष्ट हैं ?
**Options:**
- बिलकुल शंतुष्ट हैं
- बिलकुल शंतुष्ट नहीं
- कुछ हद तक शंतुष्ट हैं
- कुछ कह नहीं सकते

**Question 12:** आप अगले मुख्यमंत्री के रूप में किसे देखना चाहते हैं ?
**Options:**
- नितीश कुमार
- तेजश्वी यादव
- सम्राट चौधरी
- चिराग पासवान
- प्रशांत किशोर
- अन्य

---

### Section 3 – Observational Questions

**Question 13:** आप गाँव में रहते हैं या शहर में?
**Options:**
- गाँव
- शहर

**Question 14:** ब्लाक का नाम (आप जहाँ है उस ब्लाक का नाम चुनें)
**Note:** Extract the exact block name mentioned in the transcript

**Question 15:** गाँव / पंचायत का नाम (आप जिस गाँव/ पंचायत में है उस पंचायत का नाम चुनें)
**Note:** Extract the exact village/panchayat name mentioned in the transcript

**Question 16:** सर क्या मैं आपका मोबाइल नंबर जान सकता हूँ ?
**Note:** Extract the mobile number if provided in the transcript

---

## ANALYSIS GUIDELINES:

1. **For Questions 1-13**: Select EXACTLY ONE option from the provided list that best matches the respondent's answer
2. **For Question 14-16**: Extract the exact information (block name, village/panchayat name, mobile number) as mentioned in the transcript
3. **Contextual Understanding**: Understand variations in Hindi responses. For example:
   - "हाँ", "जी हाँ", "बिल्कुल", "ठीक है" all mean "Yes"
   - "नहीं", "जी नहीं", "बिल्कुल नहीं" all mean "No"
   - Age ranges: Listen for specific numbers and categorize appropriately
4. **Partial Answers**: If the respondent gives an incomplete or unclear answer, choose "कुछ कह नहीं सकते" or equivalent option if available


## OUTPUT FORMAT:

Return your analysis in the following JSON structure:

{
  "section_1": {
    "question_1": "selected option or Not Available",
    "question_2": "selected option or Not Available",
    "question_3": "selected option or Not Available",
    "question_4": "selected option or Not Available",
    "question_5": "selected option or Not Available",
    "question_6": "answer or Not Available"
  },
  "section_2": {
    "question_7": "selected option or Not Available",
    "question_8": "selected option or Not Available",
    "question_9": "selected option or Not Available",
    
    "question_10": "selected option or Not Available",
    "question_11": "selected option or Not Available",
    "question_12": "selected option or Not Available",
    "question_13": "selected option or Not Available"
  },
  "section_3": {
    "question_14": "selected option or Not Available",
    "question_15": "Answer or Not Available",
    "question_16": "Answer or Not Available",
    
  }
}

## IMPORTANT REMINDERS:

- **DO NOT TRANSLATE** the options - keep them in Hindi as provided
- **DO NOT INVENT** answers - only extract from the transcript. U can do a bit assumption by taking word from the transcript but DONOT GUESS COMPLETELY.
- **ENSURE VALID JSON** - proper formatting with quotes and commas
- **ONE ANSWER PER QUESTION** - select only one option from the provided list
- **EXACT OPTION MATCH** - use the exact text of the option as provided above

Now, please analyze the given Hindi transcript and provide the extracted information in the specified JSON format:
 '''
        
        self.comparison_prompt = ''' You are an expert semantic analysis system tasked with comparing two sets of survey answers in Hindi language. Your job is to evaluate whether two answers to the same question are semantically equivalent, partially equivalent, or completely different.

## CRITICAL INSTRUCTIONS:

1. **INPUT STRUCTURE**: You will receive a JSON where each question contains TWO values (either as a list or separate inputs)
   - Format: `"question_X": ["answer_1", "answer_2"]` OR separate values
   - Each question will have exactly 2 answers to compare

2. **SEMANTIC COMPARISON**: You MUST perform SEMANTIC matching, NOT exact text matching
   - Understand the MEANING and INTENT of the answers in Hindi
   - Recognize synonyms, paraphrases, and equivalent expressions
   - Consider cultural and contextual equivalence
   - Account for different ways of expressing the same information

3. **THREE EVALUATION CATEGORIES**:
   - **"matched"**: Both answers convey the SAME meaning semantically
   - **"partially matched"**: Answers have SOME overlap or similarity but are not completely the same
   - **"not matched"**: Answers are COMPLETELY DIFFERENT with no semantic overlap

4. **HANDLE "Not Available"**:
   - If BOTH answers are "Not Available" → **"matched"**
   - If ONE answer is "Not Available" and other is a valid answer → **"not matched"**

5. **LANGUAGE UNDERSTANDING**: Deep understanding of Hindi is critical
   - Recognize synonyms (e.g., "खुश" and "संतुष्ट" both mean satisfied/happy)
   - Understand different phrasings of the same concept
   - Consider regional variations and colloquial expressions

## SEMANTIC MATCHING GUIDELINES BY QUESTION TYPE:

### For Yes/No Questions (Questions 1, 8, 9):
- **"matched"**:
  - Both say "हाँ" OR both say "नहीं" OR both say "कुछ कह नहीं सकते"
  - Synonyms: "हाँ" = "जी हाँ" = "बिल्कुल" = "ठीक है"
  - Synonyms: "नहीं" = "जी नहीं" = "बिल्कुल नहीं"
- **"partially matched"**: Rare for yes/no, but could occur if one is "कुछ कह नहीं सकते" and other is conditional
- **"not matched"**: One says "हाँ" and other says "नहीं"

### For Age Range Questions (Question 2):
- **"matched"**:
  - Exact same age range: "18-30 वर्ष" = "18-30 वर्ष"
  - "बताना नहीं चाहते" = "बताना नहीं चाहते"
- **"partially matched"**:
  - Adjacent/overlapping age ranges: "31-45 वर्ष" and "46-60 वर्ष" (close but not same)
  - One specific age mentioned that falls within the range
- **"not matched"**:
  - Completely different age ranges: "18-30 वर्ष" vs "60 वर्ष से अधिक"

### For Gender (Question 3):
- **"matched"**: Both say "पुरुष" OR both say "महिला"
- **"not matched"**: One says "पुरुष" and other says "महिला"

### For Occupation (Question 4):
- **"matched"**:
  - Exact same occupation
  - Semantic equivalents: "मजदूरी" ≈ "दैनिक वेतन" (both are labor work)
  - "गृहिणी" = "हाउसवाइफ" = "घर का काम"
- **"partially matched"**:
  - Related occupations: "सरकारी नौकरी" and "निजी नौकरी" (both are jobs but different sectors)
  - Broad category match with some difference
- **"not matched"**:
  - Completely different: "कृषि" vs "छात्र"

### For Religion (Question 5):
- **"matched"**: Exact same religion
- **"not matched"**: Different religions
- Note: "बताना नहीं चाहते" only matches with itself

### For Caste (Question 6):
- **"matched"**:
  - Exact same caste name
  - Different spellings of same caste (e.g., variations in Hindi spelling)
- **"partially matched"**:
  - Same caste category but different sub-castes
- **"not matched"**: Completely different castes

### For MLA Name (Question 7):
- **"matched"**:
  - Both say "MLA का नाम नहीं पता"
  - Both say "MLA का नाम सही बताया" (assuming they named the same person)
  - Both say "MLA का नाम गलत बताया"
- **"not matched"**: Different categories selected

### For Political Party Questions (Questions 10, 11):
- **"matched"**:
  - Exact same party/alliance
  - Semantic equivalents: "JDU" = "NDA" (if JDU is part of NDA)
  - "महागठबंधन" = "MGB"
- **"partially matched"**:
  - Parties from same alliance but different specific parties mentioned
  - "कह नहीं सकते" with a specific party (uncertainty vs decision)
- **"not matched"**:
  - Completely different parties/alliances: "NDA" vs "महागठबंधन"
  - "NOTA" vs any specific party

### For Satisfaction Questions (Question 12):
- **"matched"**:
  - Exact same level: "बिलकुल शंतुष्ट हैं" = "बिलकुल शंतुष्ट हैं"
- **"partially matched"**:
  - Adjacent levels: "बिलकुल शंतुष्ट हैं" and "कुछ हद तक शंतुष्ट हैं" (both positive but different intensity)
  - "बिलकुल शंतुष्ट नहीं" and "कुछ हद तक शंतुष्ट हैं" (one negative, one mixed)
- **"not matched"**:
  - Opposite extremes: "बिलकुल शंतुष्ट हैं" vs "बिलकुल शंतुष्ट नहीं"

### For CM Preference (Question 13):
- **"matched"**:
  - Exact same name
  - Name variations/spellings of same person
- **"partially matched"**: Rare, unless there's ambiguity in name
- **"not matched"**: Different persons

### For Village/City (Question 14):
- **"matched"**: Both say "गाँव" OR both say "शहर"
- **"not matched"**: One says "गाँव" and other says "शहर"

### For Block/Village/Panchayat Names (Questions 15, 16):
- **"matched"**:
  - Exact same name
  - Minor spelling variations of same place
  - Abbreviations vs full names of same place
- **"partially matched"**:
  - Similar sounding names but might be different places
  - One mentions broader area, other mentions specific sub-area
- **"not matched"**: Completely different place names

### For Mobile Number (Question 17):
- **"matched"**:
  - Exact same number
  - Same number with country code vs without country code
- **"not matched"**: Different numbers

## SEMANTIC EQUIVALENCE EXAMPLES:

**Example 1 - Occupation:**
- Answer 1: "हाउसवाइफ / गृहिणी"
- Answer 2: "घर का काम करती हूँ"
- Result: **"matched"** (same meaning - housewife)

**Example 2 - Age:**
- Answer 1: "31-45 वर्ष"
- Answer 2: "46-60 वर्ष"
- Result: **"partially matched"** (adjacent ranges, close but not same)

**Example 3 - Political Party:**
- Answer 1: "JDU | NDA"
- Answer 2: "महागठबंधन | MGB"
- Result: **"not matched"** (opposite alliances)

**Example 4 - Satisfaction:**
- Answer 1: "बिलकुल शंतुष्ट हैं"
- Answer 2: "कुछ हद तक शंतुष्ट हैं"
- Result: **"partially matched"** (both positive but different intensity)

**Example 5 - Yes/No:**
- Answer 1: "हाँ"
- Answer 2: "जी हाँ, बिल्कुल"
- Result: **"matched"** (both mean yes)

**Example 6 - Not Available:**
- Answer 1: "Not Available"
- Answer 2: "Not Available"
- Result: **"matched"** (both unavailable)

**Example 7 - Mixed:**
- Answer 1: "नितीश कुमार"
- Answer 2: "Not Available"
- Result: **"not matched"** (one has answer, other doesn't)

## OUTPUT FORMAT:

Return your comparison results in the following JSON structure:

{
  "section_1": {
    "question_1": "matched / partially matched / not matched",
    "question_2": "matched / partially matched / not matched",
    "question_3": "matched / partially matched / not matched",
    "question_4": "matched / partially matched / not matched",
    "question_5": "matched / partially matched / not matched",
    "question_6": "matched / partially matched / not matched"
  },
  "section_2": {
    "question_7": "matched / partially matched / not matched",
    "question_8": "matched / partially matched / not matched",
    "question_9": "matched / partially matched / not matched",
    "question_9_1": "matched / partially matched / not matched",
    "question_10": "matched / partially matched / not matched",
    "question_11": "matched / partially matched / not matched",
    "question_12": "matched / partially matched / not matched",
    "question_13": "matched / partially matched / not matched"
  },
  "section_3": {
    "question_14": "matched / partially matched / not matched",
    "question_15": "matched / partially matched / not matched",
    "question_16": "matched / partially matched / not matched",
    "question_17": "matched / partially matched / not matched"
  },
  "summary": {
    "total_questions": 17,
    "matched": 0,
    "partially_matched": 0,
    "not_matched": 0
  }
}

## ANALYSIS WORKFLOW:

1. **Step 1**: Parse the input JSON and identify the two answers for each question
2. **Step 2**: For each question, extract Answer 1 and Answer 2
3. **Step 3**: Analyze the SEMANTIC meaning of both answers in Hindi context
4. **Step 4**: Determine if they are "matched", "partially matched", or "not matched"
5. **Step 5**: Apply the appropriate guidelines based on question type
6. **Step 6**: Calculate summary statistics
7. **Step 7**: Return valid JSON output

## IMPORTANT REMINDERS:

- **SEMANTIC ANALYSIS**: Focus on MEANING, not exact text matching
- **HINDI CONTEXT**: Deeply understand Hindi language nuances and cultural context
- **BE CONSISTENT**: Apply the same standards across all questions
- **BE FAIR**: Don't be too strict - recognize equivalent expressions
- **BE ACCURATE**: Consider the question type and apply appropriate matching logic
- **VALID JSON ONLY**: Ensure proper formatting with correct quotes and commas
- **USE EXACT VALUES**: Only use "matched", "partially matched", or "not matched" - no other values
- **BOTH ANSWERS MATTER**: You must compare TWO answers for each question

## SPECIAL NOTES:

- If input has a LIST format `["answer_1", "answer_2"]`, compare the two items in the list
- If answers are provided separately, compare them accordingly
- Always provide a summary with counts of matched, partially matched, and not matched
- Be particularly careful with political questions as they have semantic relationships (parties in alliances)

Now, please analyze the  JSON with answer pairs and provide the semantic comparison results in the specified JSON format:
 '''

    def _load_audio_to_base64(self, file_path: str) -> Tuple[str, str]:
        """Convert audio file to base64 encoding and determine mime type"""
        with open(file_path, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode("utf-8")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        mime_type = {
            '.m4a': 'audio/m4a',
            '.mp4': 'audio/mp4',
            '.mp3': 'audio/mp3',
            '.wav': 'audio/wav'
        }.get(file_extension, 'application/octet-stream')
        
        return audio_data, mime_type

    def _load_json_to_base64(self, file_path: str) -> str:
        """Convert JSON file to base64 encoding"""
        with open(file_path, "rb") as json_file:
            return base64.standard_b64encode(json_file.read()).decode("utf-8")

    def _clean_json_output(self, content: str) -> str:
        """Clean JSON output by removing markdown code blocks"""
        lines = content.splitlines(keepends=True)
        if len(lines) >= 2:
            lines = lines[1:-1]
        return ''.join(lines)

    def _save_output(self, content: str, output_path: str, clean: bool = True) -> None:
        """Save content to file"""
        if clean:
            content = self._clean_json_output(content)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _merge_survey_jsons(self, json1_path: str, json2_path: str, output_path: str) -> None:
        """Merge two survey JSONs side by side"""
        with open(json1_path, 'r', encoding='utf-8') as f:
            json1 = json.load(f)
        with open(json2_path, 'r', encoding='utf-8') as f:
            json2 = json.load(f)

        merged_json = {}
        all_sections = set(json1.keys()) | set(json2.keys())

        for section_key in all_sections:
            merged_json[section_key] = {}
            section1 = json1.get(section_key, {})
            section2 = json2.get(section_key, {})
            all_questions = set(section1.keys()) | set(section2.keys())

            for question_key in all_questions:
                value1 = section1.get(question_key, "Not Available")
                value2 = section2.get(question_key, "Not Available")
                merged_json[section_key][question_key] = [value1, value2]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_json, f, ensure_ascii=False, indent=2)

    def _create_final_output(self, answers_path: str, quality_path: str, 
                            comparison_path: str, output_path: str) -> None:
        """Merge three JSONs into final comprehensive output"""
        with open(answers_path, 'r', encoding='utf-8') as f:
            answers = json.load(f)
        with open(quality_path, 'r', encoding='utf-8') as f:
            quality = json.load(f)
        with open(comparison_path, 'r', encoding='utf-8') as f:
            comparison = json.load(f)

        final_output = {}
        for section_key in answers.keys():
            final_output[section_key] = {}
            for question_key in answers[section_key].keys():
                ans = answers[section_key][question_key]
                qual = quality.get("quality_assessment", {}).get(question_key, "Not Available")
                comp = comparison.get(section_key, {}).get(question_key, "Not Available")
                final_output[section_key][question_key] = ans + [qual, comp]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)

    def process_audio(
        self,
        audio_file_path: str,
        json_path_2: str,
        output_dir: str = "./output",
        transcription_filename: str = "audio_transcript.json",
        evaluation_filename: str = "evaluation_output.json",
        analysis_filename: str = "audio_analysis.json",
        merged_filename: str = "merged_survey.json",
        comparison_filename: str = "comparison_output.json",
        final_filename: str = "final_output.json",
        audio_mime_type: str = "audio/m4a"
    ) -> dict:
        """
        Execute the complete 6-step analysis pipeline
        
        Args:
            audio_file_path: Path to Hindi audio file
            json_path_2: Path to agent's survey JSON
            output_dir: Directory to save output files
            transcription_filename: Name for transcription output file
            evaluation_filename: Name for evaluation output file
            analysis_filename: Name for analysis output file
            merged_filename: Name for merged survey file
            comparison_filename: Name for comparison output file
            final_filename: Name for final output file
            audio_mime_type: MIME type of the audio file
            
        Returns:
            Dictionary containing all output paths and loaded content
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output paths
        transcript_path = os.path.join(output_dir, transcription_filename)
        evaluation_path = os.path.join(output_dir, evaluation_filename)
        analysis_path = os.path.join(output_dir, analysis_filename)
        merged_path = os.path.join(output_dir, merged_filename)
        comparison_path = os.path.join(output_dir, comparison_filename)
        final_path = os.path.join(output_dir, final_filename)

        # Step 1: Transcribe audio
        print("Step 1/6: Transcribing audio...")
        audio_data, detected_mime = self._load_audio_to_base64(audio_file_path)
        mime_type = audio_mime_type if audio_mime_type != "audio/m4a" else detected_mime
        
        contents_transcription = [
            {'mime_type': mime_type, 'data': audio_data},
            self.transcription_prompt
        ]
        
        response = self.model_lite.generate_content(
            contents_transcription,
            generation_config=self.generation_config
        )
        self._save_output(response.text, transcript_path, clean=True)
        print(f"   -> Saved transcript to {transcript_path}")

        # Step 2: Evaluate agent questions
        print("Step 2/6: Evaluating agent performance...")
        transcript_b64 = self._load_json_to_base64(transcript_path)
        
        contents_evaluation = [
            {'mime_type': 'text/plain', 'data': transcript_b64},
            self.evaluation_prompt
        ]
        
        response = self.model_lite.generate_content(
            contents_evaluation,
            generation_config=self.generation_config
        )
        self._save_output(response.text, evaluation_path, clean=True)
        print(f"   -> Saved evaluation to {evaluation_path}")

        # Step 3: Analyze transcript content
        print("Step 3/6: Analyzing transcript...")
        contents_analysis = [
            {'mime_type': 'text/plain', 'data': transcript_b64},
            self.analysis_prompt
        ]
        
        response = self.model_pro.generate_content(
            contents_analysis,
            generation_config=self.generation_config
        )
        self._save_output(response.text, analysis_path, clean=True)
        print(f"   -> Saved analysis to {analysis_path}")

        # Step 4: Merge agent and analysis JSONs
        print("Step 4/6: Merging survey responses...")
        self._merge_survey_jsons(json_path_2, analysis_path, merged_path)
        print(f"   -> Saved merged data to {merged_path}")

        # Step 5: Compare merged answers
        print("Step 5/6: Comparing responses...")
        merged_b64 = self._load_json_to_base64(merged_path)
        
        contents_comparison = [
            {'mime_type': 'text/plain', 'data': merged_b64},
            self.comparison_prompt
        ]
        
        response = self.model_lite.generate_content(
            contents_comparison,
            generation_config=self.generation_config
        )
        self._save_output(response.text, comparison_path, clean=True)
        print(f"   -> Saved comparison to {comparison_path}")

        # Step 6: Create final output
        print("Step 6/6: Generating final output...")
        self._create_final_output(merged_path, evaluation_path, comparison_path, final_path)
        print(f"   -> Saved final output to {final_path}")

        # Load all outputs for return
        result = {
            'transcription_path': transcript_path,
            'evaluation_path': evaluation_path,
            'analysis_path': analysis_path,
            'merged_path': merged_path,
            'comparison_path': comparison_path,
            'final_path': final_path
        }

        # Load JSON content
        for key in ['transcription', 'evaluation', 'analysis', 'merged', 'comparison', 'final']:
            path_key = f"{key}_path"
            try:
                with open(result[path_key], 'r', encoding='utf-8') as f:
                    result[key] = json.load(f)
            except json.JSONDecodeError:
                with open(result[path_key], 'r', encoding='utf-8') as f:
                    result[key] = f.read()

        print("\n✓ Pipeline completed successfully!")
        return result


def run_pipeline(audio_path, json_path_2, json_path_1):
    """
    Run the complete 6-step pipeline with audio file, agent JSON, and Gemini credentials
    
    Args:
        audio_path: Path to audio file
        json_path_2: Path to agent's survey JSON file
        json_path_1: Path to Gemini API credentials JSON file
        
    Returns:
        Tuple of (transcription_path, analysis_path, final_path, transcription_content, 
                  analysis_content, final_content)
    """
    # Use Gemini JSON as credentials
    credentials_path = str(json_path_1)
    
    # Create output directory
    out_dir = tempfile.mkdtemp(prefix="audio-analysis-pipeline-")
    
    # Initialize pipeline
    pipeline = AudioAnalysisPipeline(credentials_path=credentials_path)
    
    # Process audio with full 6-step pipeline
    result = pipeline.process_audio(
        audio_file_path=str(audio_path),
        json_path_2=str(json_path_2),
        output_dir=out_dir
    )
    
    return (
        result['transcription_path'],
        result['analysis_path'],
        result['final_path'],
        result['transcription'],
        
        result['final']
    )


# Example usage
if __name__ == '__main__':
    # For direct script execution
    pipeline = AudioAnalysisPipeline(
        credentials_path="path/to/gemini_credentials.json"
    )
    
    result = pipeline.process_audio(
        audio_file_path="path/to/audio.m4a",
        json_path_2="path/to/agent_data.json",
        output_dir="./output"
    )
    
    print(f"Final output saved to: {result['final_path']}")
