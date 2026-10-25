from src.interview import Question, score_interview

questions = [
    Question("Tell me about a data project you delivered.", "execution", ["data", "python", "analysis", "result"], 1.2),
    Question("How do you handle competing priorities?", "planning", ["priority", "stakeholder", "deadline"], 1.0),
]
answers = [
    "I built a Python data analysis workflow, analysed customer data and improved reporting time by 30 percent.",
    "I rank each priority by deadline and impact, then communicate trade-offs with every stakeholder.",
]

result = score_interview(questions, answers)
print(f"MockHire final score: {result['final_score']}/100")
for i, item in enumerate(result["evaluations"], 1):
    print(i, item)
