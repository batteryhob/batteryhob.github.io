---
layout: post
title: Applying Reinforcement Learning to LLM Agents - From Theory to Practice
date: 2025-11-09 01:00:00 +0900
author: 전지호
tags: ai llm reinforcement-learning rl agent machine-learning rlhf research
excerpt: Learn how to make LLM agents learn from past experiences and progressively improve using reinforcement learning techniques. A complete guide from academic research to practical implementation.
use_math: true
toc: true
description: How to apply reinforcement learning to LLM agents - RLHF, ReAct, Reflexion, and practical implementation guide
lang: en
ref: llm-agent-rl
---

## Introduction

Large Language Models (LLMs) have evolved beyond simple text generation to become **agents** capable of performing complex tasks. However, pre-trained models alone struggle to achieve optimal performance on specific tasks.

Using **Reinforcement Learning (RL)**, we can enable LLM agents to interact with their environment and progressively improve. This post covers everything from theory to practical implementation.

## Core Idea: One-Line Summary

> **"LLM performs a task, records whether the result was good or bad, and does better next time"**

---

## 1. Why Do LLM Agents Need RL?

### Limitations of LLMs

**Problems with Pre-trained Models:**
- Only learn general patterns (not optimized for specific tasks)
- Difficult to incorporate user feedback in real-time
- Cannot improve through trial-and-error
- Parameters are frozen, preventing learning during conversations

### RL Solutions

**What RL Provides:**
- Learning through environmental interaction
- Behavior optimization via reward signals
- Progressive improvement through trial-and-error
- Strategy learning for achieving long-term goals

---

## 2. How Are LLMs Trained?

First, we need to understand how modern LLMs like Claude and ChatGPT are actually built.

### RLHF (Reinforcement Learning from Human Feedback)

This is the standard training method for modern LLMs.

#### Training Pipeline

```
1. Pre-training
   ↓
   Learn language patterns from massive text data

2. Supervised Fine-tuning
   ↓
   Fine-tune on high-quality conversation examples

3. Reward Model Training
   ↓
   Humans compare and evaluate multiple responses
   "Response A is better than Response B"
   → Train a model to predict good responses

4. RL Optimization (PPO Algorithm)
   ↓
   - LLM generates responses
   - Reward Model scores them
   - Update parameters toward higher scores
```

#### Key Papers

**InstructGPT (OpenAI, 2022)**
```python
# Conceptual code
def rlhf_training():
    # 1. Generate response
    response = llm.generate(prompt)

    # 2. Calculate reward
    reward = reward_model.score(prompt, response)

    # 3. Update policy with PPO
    loss = -reward * log_prob(response)
    llm.update(loss)
```

**Constitutional AI (Anthropic, 2022)**
- Principle-based learning
- Self-critique and revision
- Balance between safety and helpfulness

**Key Characteristics:**
- Offline learning (completed before deployment)
- Parameters frozen during actual use
- No learning during conversations

---

## 3. How Are LLM Agents Different?

### Agent Characteristics

**LLM vs Agent:**

| Feature | Regular LLM | LLM Agent |
|---------|------------|-----------|
| Operation | One-shot response | Iterative interaction |
| Environment | X | O (tools, APIs, file system) |
| Feedback | Only during training | Real-time |
| Memory | Context only | External storage possible |
| Improvement | Requires retraining | Runtime improvement possible |

### Problems Agents Face

```python
# Agent task example
Task: "Fix this bug"

Try 1:
  Action 1: Only modify file A
  Result: Failure (related to other files)

Try 2:
  Action 1: Search for related files
  Action 2: Modify files A, B, C together
  Result: Success!
```

**Problem:** Regular LLMs can't utilize Try 1's failure next time.

**Solution:** Learn and reuse experiences with RL techniques!

---

## 4. RL Research for Agents

### A. ReAct (2022)

**"Reasoning and Acting in Language Models"** - Yao et al.

#### Core Idea

Alternating between Thought and Action

```python
# ReAct pattern
loop:
  Thought: "I should check the error log first to find the bug"
  Action: read_file("error.log")
  Observation: "TypeError at line 45"

  Thought: "I should check line 45"
  Action: read_file("main.py", line=45)
  Observation: "Wrong variable type"

  Thought: "I need to fix the type"
  Action: edit_file("main.py", line=45, new_code="...")
  Observation: "Edit complete"
```

#### RL Connection

- Include successful past trajectories in prompts
- Learn behavior patterns through few-shot learning
- Use failure cases as negative examples

---

### B. Reflexion (2023)

**"Language Agents with Verbal Reinforcement Learning"** - Shinn et al.

#### Core Idea

Learn from failures and store verbal feedback

```python
# Reflexion process
class ReflexionAgent:
    def __init__(self):
        self.memory = []  # Store past experiences

    def solve_task(self, task):
        # 1. Search relevant experiences
        past_attempts = self.search_memory(task)

        # 2. Execute task
        result = self.execute(task, context=past_attempts)

        # 3. Self-reflection (on failure)
        if not result.success:
            reflection = self.reflect(task, result)
            self.memory.append({
                'task': task,
                'attempt': result.actions,
                'outcome': 'failed',
                'reflection': reflection
            })

        return result

    def reflect(self, task, result):
        """Analyze failure causes"""
        prompt = f"""
        Task: {task}
        Actions taken: {result.actions}
        Error: {result.error}

        What went wrong and how to improve?
        """
        return llm.generate(prompt)
```

#### Real Example

```
Try 1:
  Task: "Crawl news from website"
  Actions: [Direct requests.get() call]
  Result: 403 Forbidden
  Reflection: "User-Agent header was needed.
               Must set headers next time"

Try 2:
  Task: "Crawl news from website"
  Reference previous reflection
  Actions: [requests.get() with User-Agent]
  Result: Success!
```

#### RL Terminology Mapping

- **State**: Current task + past experiences
- **Action**: Code/commands generated by LLM
- **Reward**: Success/failure
- **Policy**: Action selection considering reflection

---

### C. Voyager (2023)

**"An Open-Ended Embodied Agent with LLMs"** - Wang et al.

#### Core Idea

Save successful code as "skills" and reuse them

```python
# Voyager skill library
class SkillLibrary:
    def __init__(self):
        self.skills = {}

    def add_skill(self, name, code, context):
        """Save successful code as skill"""
        self.skills[name] = {
            'code': code,
            'success_rate': 1.0,
            'context': context,
            'dependencies': []
        }

    def search_skills(self, task):
        """Search for relevant skills"""
        # Find related skills by vector similarity
        return vector_search(task, self.skills)

    def compose_skills(self, task):
        """Compose multiple skills"""
        relevant_skills = self.search_skills(task)
        return combine(relevant_skills)

# Usage example
skill_library = SkillLibrary()

# First task
task1 = "Mine wood"
code1 = generate_code(task1)
if execute(code1).success:
    skill_library.add_skill("mine_wood", code1, task1)

# Second task (reuse skill)
task2 = "Build house"
wood_skill = skill_library.search_skills("need wood")
code2 = generate_code(task2, existing_skills=[wood_skill])
```

#### Real Application in Minecraft

```python
# Initially: no skills
solve("Find diamond")
  → Failure (no tools)

# Learned skills
skill_library = {
    "craft_pickaxe": {...},  # Make pickaxe
    "mine_stone": {...},      # Mine stone
    "find_cave": {...},       # Find cave
}

# Retry: compose skills
solve("Find diamond")
  1. craft_pickaxe()
  2. find_cave()
  3. mine_diamond()
  → Success!
```

#### RL Connection

- **Hierarchical RL**: Skills = Options
- **Curriculum Learning**: Simple skills to complex skills
- **Transfer Learning**: Reuse learned skills

---

### D. WebGPT (2021)

**Pioneer of Online RL** - OpenAI

#### Core Idea

Turn web browsing into an RL environment

```python
# WebGPT Environment
class WebEnvironment:
    actions = [
        "search(query)",      # Search
        "click(link_id)",     # Click link
        "scroll(direction)",  # Scroll
        "quote(text)",        # Quote
        "answer(text)"        # Submit answer
    ]

    def step(self, action):
        # Execute action
        observation = execute_browser_action(action)

        # Reward (human evaluation)
        reward = human_feedback.score(observation)

        return observation, reward

# RL training
for episode in range(num_episodes):
    state = env.reset(question)

    while not done:
        action = agent.choose_action(state)
        next_state, reward = env.step(action)

        # Update policy
        agent.update(state, action, reward, next_state)
```

#### Features

- **Real-time learning**: Immediate improvement from user feedback
- **Reward function**: Answer accuracy + citation quality
- **Exploration**: Try new search strategies

---

### E. In-Context Reinforcement Learning (2023)

**Acting as if learning without parameter updates**

#### Algorithm Distillation

```python
# Simulate RL algorithm in prompt
def in_context_rl(task):
    prompt = """
    You are an agent that learns through trial and error.

    Previous attempts:
    Try 1: Action=A, Reward=-1 (failed)
    Try 2: Action=B, Reward=-1 (failed)
    Try 3: Action=C, Reward=+1 (success!)
    Try 4: Action=C, Reward=+1 (success!)

    Pattern: Action C produces good results.

    Now a new situation:
    {task}

    Which action would you choose?
    """
    return llm.generate(prompt)
```

#### Key Insight

LLMs can "learn" RL algorithms from prompts:
- Exploration vs Exploitation
- Credit assignment
- Policy improvement

**Advantages:**
- No parameter updates needed
- Fast adaptation
- General-purpose across tasks

**Disadvantages:**
- Context length limit
- Lack of long-term memory

---

## 5. Practical Implementation Guide

Now let's explore methods you can actually implement.

### Method 1: Simple Memory-Based (Easiest)

```python
import json
from typing import List, Dict
from datetime import datetime

class SimpleMemoryAgent:
    """Agent that stores and reuses past experiences"""

    def __init__(self, memory_file='agent_memory.json'):
        self.memory_file = memory_file
        self.memory = self.load_memory()

    def load_memory(self) -> List[Dict]:
        """Load memory file"""
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_memory(self):
        """Save memory file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def find_similar_experiences(self, task: str, top_k=3):
        """Search for similar past experiences"""
        # Simple keyword matching (use embeddings in practice)
        task_words = set(task.lower().split())

        scored = []
        for exp in self.memory:
            exp_words = set(exp['task'].lower().split())
            similarity = len(task_words & exp_words) / len(task_words | exp_words)
            scored.append((similarity, exp))

        scored.sort(reverse=True)
        return [exp for _, exp in scored[:top_k]]

    def execute_task(self, task: str):
        """Execute task"""
        # 1. Search past experiences
        similar = self.find_similar_experiences(task)

        # 2. Prioritize successful patterns
        successful_patterns = [
            exp for exp in similar
            if exp['result'] == 'success'
        ]

        # 3. Choose action
        if successful_patterns:
            print(f"✅ Found past success: {len(successful_patterns)} cases")
            action = self.use_successful_pattern(successful_patterns[0])
        else:
            print("🔍 Trying new approach...")
            action = self.explore_new_approach(task)

        # 4. Execute
        result = self.run_action(action)

        # 5. Save to memory
        self.memory.append({
            'task': task,
            'action': action,
            'result': 'success' if result else 'failure',
            'timestamp': datetime.now().isoformat(),
            'score': 1 if result else -1
        })

        self.save_memory()
        return result

    def use_successful_pattern(self, experience):
        """Reuse successful pattern"""
        return experience['action']

    def explore_new_approach(self, task):
        """Explore new approach"""
        # Ask LLM
        return llm_generate(task)

    def run_action(self, action):
        """Actually execute action"""
        # Implementation needed
        pass

# Usage example
agent = SimpleMemoryAgent()

# First attempt
agent.execute_task("Fix type error in Python file")
# → New approach

# Second attempt (similar task)
agent.execute_task("Fix type error in TypeScript file")
# → Utilize past success!
```

---

### Method 2: Reward-Based Priority

```python
from collections import defaultdict
import random

class RewardBasedAgent:
    """Agent that selects actions based on reward scores"""

    def __init__(self, epsilon=0.2):
        self.action_scores = defaultdict(lambda: {'total': 0, 'count': 0})
        self.epsilon = epsilon  # Exploration rate

    def get_action_value(self, action):
        """Calculate average reward for action"""
        stats = self.action_scores[action]
        if stats['count'] == 0:
            return 0  # Return 0 if never tried
        return stats['total'] / stats['count']

    def choose_action(self, available_actions):
        """Choose action with epsilon-greedy strategy"""

        # Exploration
        if random.random() < self.epsilon:
            action = random.choice(available_actions)
            print(f"🔍 Explore: {action}")
            return action

        # Exploitation
        best_action = max(
            available_actions,
            key=self.get_action_value
        )
        print(f"🎯 Exploit: {best_action} (score: {self.get_action_value(best_action):.2f})")
        return best_action

    def update_score(self, action, reward):
        """Update reward for action"""
        self.action_scores[action]['total'] += reward
        self.action_scores[action]['count'] += 1

        avg = self.get_action_value(action)
        print(f"📊 {action} updated: avg reward = {avg:.2f}")

# Usage example
agent = RewardBasedAgent(epsilon=0.2)

# Bug fixing scenario
actions = [
    "modify single file only",
    "search and modify all related files",
    "write tests first then fix"
]

for episode in range(10):
    action = agent.choose_action(actions)

    # Execute and get reward
    if action == "write tests first then fix":
        reward = 1  # High success rate
    elif action == "search and modify all related files":
        reward = 0.5  # Medium
    else:
        reward = -0.5  # Low success rate

    agent.update_score(action, reward)

# Result: "write tests first" gets highest score
```

---

### Method 3: Q-Learning Based (Advanced)

```python
class QLearningAgent:
    """Learn optimal policy with Q-learning"""

    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.2):
        self.q_table = {}  # (state, action) -> Q-value
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate

    def get_q_value(self, state, action):
        """Look up Q-value"""
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state, available_actions):
        """Choose action with epsilon-greedy"""

        # Exploration
        if random.random() < self.epsilon:
            return random.choice(available_actions)

        # Exploitation: select action with max Q-value
        q_values = [
            (action, self.get_q_value(state, action))
            for action in available_actions
        ]
        return max(q_values, key=lambda x: x[1])[0]

    def update(self, state, action, reward, next_state, next_actions):
        """Q-learning update"""

        # Current Q-value
        old_q = self.get_q_value(state, action)

        # Max Q-value of next state
        if next_actions:
            max_next_q = max(
                self.get_q_value(next_state, a)
                for a in next_actions
            )
        else:
            max_next_q = 0  # Terminal state

        # Q-learning update formula
        new_q = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)

        self.q_table[(state, action)] = new_q

        print(f"Q({state}, {action}): {old_q:.2f} → {new_q:.2f}")

# Practical example: Code debugging agent
agent = QLearningAgent()

# State: error type
# Action: debugging strategy
states = ["TypeError", "ValueError", "AttributeError"]
actions = {
    "TypeError": ["add type check", "convert type", "fix interface"],
    "ValueError": ["validate input", "add exception handling", "set default"],
    "AttributeError": ["check attribute exists", "fix initialization", "add null check"]
}

# Training
for episode in range(100):
    state = random.choice(states)
    action = agent.choose_action(state, actions[state])

    # Simulation: certain actions are more effective
    if (state == "TypeError" and action == "fix interface") or \
       (state == "ValueError" and action == "validate input") or \
       (state == "AttributeError" and action == "add null check"):
        reward = 1
        next_state = None  # Success
    else:
        reward = -0.1
        next_state = state  # Continue

    next_actions = actions[next_state] if next_state else []
    agent.update(state, action, reward, next_state, next_actions)

# Test learned policy
print("\nOptimal policy:")
for state in states:
    best_action = agent.choose_action(state, actions[state])
    print(f"{state} → {best_action}")
```

---

### Method 4: Vector DB + Embeddings (Practical)

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class VectorMemoryAgent:
    """Embedding-based experience search"""

    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.experiences = []
        self.embeddings = []

    def add_experience(self, task, action, result, reflection=""):
        """Add experience"""
        experience = {
            'task': task,
            'action': action,
            'result': result,
            'reflection': reflection
        }

        # Generate embedding
        text = f"{task} {action} {reflection}"
        embedding = self.encoder.encode(text)

        self.experiences.append(experience)
        self.embeddings.append(embedding)

    def find_similar(self, query, top_k=3, min_similarity=0.3):
        """Search for similar experiences"""
        if not self.experiences:
            return []

        # Query embedding
        query_embedding = self.encoder.encode(query)

        # Calculate similarity
        similarities = cosine_similarity(
            [query_embedding],
            self.embeddings
        )[0]

        # Select top-K
        indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in indices:
            if similarities[idx] >= min_similarity:
                results.append({
                    **self.experiences[idx],
                    'similarity': similarities[idx]
                })

        return results

    def solve_with_memory(self, task):
        """Problem solving with memory"""
        # 1. Search for similar past experiences
        similar_exps = self.find_similar(task, top_k=3)

        if similar_exps:
            print(f"📚 Found {len(similar_exps)} relevant experiences:")
            for i, exp in enumerate(similar_exps, 1):
                print(f"  {i}. {exp['task'][:50]}... "
                      f"(similarity: {exp['similarity']:.2f}, "
                      f"result: {exp['result']})")

        # 2. Prioritize successful experiences
        successful = [e for e in similar_exps if e['result'] == 'success']

        if successful:
            print(f"✅ Using successful experience!")
            base_action = successful[0]['action']
        else:
            print(f"🆕 Need new approach")
            base_action = self.generate_new_action(task)

        return base_action

    def generate_new_action(self, task):
        """Generate new action (use LLM)"""
        # Actually use LLM
        return f"New strategy: {task}"

# Usage example
agent = VectorMemoryAgent()

# Accumulate experiences
agent.add_experience(
    task="Fix React component rendering error",
    action="Fix useEffect dependency array",
    result="success",
    reflection="Empty dependency array caused infinite loop"
)

agent.add_experience(
    task="Vue component not updating",
    action="Change to use reactive()",
    result="success",
    reflection="Object property changes weren't detected"
)

agent.add_experience(
    task="React state update error",
    action="Use setState functional update",
    result="success",
    reflection="Needed update based on previous state"
)

# Solve new problem
new_task = "Resolve React Hook dependency warning"
solution = agent.solve_with_memory(new_task)
# → "React component rendering error" experience found as similar!
```

---

## 6. Understanding Through Real-Life Analogy

### Chef Agent

```
Agent = Chef
Task = Make pasta
Action = Ingredient selection, cooking method
Reward = Taste evaluation

Episode 1:
  Action: 1 spoon of salt
  Feedback: "Too bland" (-1 point)
  Memory: "1 spoon salt = failure"

Episode 2:
  Memory reference: "Last time 1 spoon didn't work"
  Action: 3 spoons of salt
  Feedback: "Perfect!" (+1 point)
  Memory: "3 spoons salt = success"

Episode 3 onwards:
  Memory reference: "3 spoons optimal"
  Action: Automatically use 3 spoons
  Feedback: Continues to get good evaluation

→ This is reinforcement learning!
```

---

## 7. Comparison of Major Research

| Method | Learning Type | Memory | Real-time Learning | Pros | Cons |
|--------|--------------|--------|-------------------|------|------|
| **RLHF** | Offline RL | X | X | Safe, high quality | Fixed after deployment |
| **ReAct** | Prompting | In-context | X | Simple, interpretable | Short memory |
| **Reflexion** | Episodic | Text storage | △ | Learn from failure | Storage space |
| **Voyager** | Skill library | Code storage | △ | Reusability | Domain-specific |
| **In-Context RL** | Few-shot | Context | X | Fast adaptation | Length limit |
| **WebGPT** | Online RL | X | O | Continuous improvement | Cost, safety |

---

## 8. Implementation Considerations

### A. Reward Shaping

```python
# Bad reward
reward = 1 if task_complete else 0  # Sparse reward

# Good reward
reward = 0
if task_complete:
    reward += 1.0
if test_passed:
    reward += 0.5
if code_quality_good:
    reward += 0.3
if fast_execution:
    reward += 0.2
# Dense reward!
```

### B. Exploration vs Exploitation

```python
def epsilon_greedy(epsilon, iteration):
    """Gradually decrease exploration"""
    return epsilon * (0.99 ** iteration)

# Initial: epsilon=0.5 (50% exploration)
# After 100 iterations: epsilon=0.18 (18% exploration)
# After 500 iterations: epsilon=0.003 (mostly exploitation)
```

### C. Safety Measures

```python
class SafeAgent:
    def execute_action(self, action):
        # 1. Filter dangerous actions
        if is_dangerous(action):
            print("⚠️ Dangerous action blocked")
            return None

        # 2. Test in sandbox
        test_result = run_in_sandbox(action)
        if not test_result.safe:
            print("⚠️ Unsafe result")
            return None

        # 3. Actually execute
        return execute(action)
```

---

## 9. Future Directions

### A. Efficient Memory

```python
# Hierarchical memory
class HierarchicalMemory:
    def __init__(self):
        self.short_term = []  # Recent 10
        self.long_term_index = VectorDB()  # Important ones only
        self.skill_library = {}  # Reusable skills

    def add(self, experience):
        self.short_term.append(experience)

        # Evaluate importance
        if is_important(experience):
            self.long_term_index.add(experience)

        # Extract skills
        if is_reusable(experience):
            skill = extract_skill(experience)
            self.skill_library[skill.name] = skill
```

### B. Multimodal Expansion

```python
# Image + text experiences
experience = {
    'task': "Fix UI bug",
    'screenshot_before': img_before,
    'screenshot_after': img_after,
    'code_changes': diff,
    'result': 'success'
}
```

### C. Collaborative Learning

```python
# Multiple agents share experiences
class SharedMemory:
    def __init__(self):
        self.global_experiences = []

    def contribute(self, agent_id, experience):
        """Agent shares experience"""
        self.global_experiences.append({
            'agent': agent_id,
            'experience': experience
        })

    def learn_from_others(self, agent_id):
        """Learn from other agents' experiences"""
        others = [
            exp for exp in self.global_experiences
            if exp['agent'] != agent_id
        ]
        return others
```

---

## 10. Practical Project Ideas

### Beginner: Simple Memory Bot

```python
# GitHub issue resolver bot
class IssueResolverBot:
    def solve_issue(self, issue):
        # 1. Search for similar past issues
        similar = self.find_similar_issues(issue)

        # 2. Apply solution
        if similar and similar[0].solved:
            solution = similar[0].solution
        else:
            solution = llm_generate_solution(issue)

        # 3. Save result
        self.save_experience(issue, solution)
```

### Intermediate: Code Review Agent

```python
class CodeReviewAgent:
    def review(self, pull_request):
        # 1. Learn from past review patterns
        patterns = self.learn_from_past_reviews()

        # 2. Apply
        issues = self.detect_issues(pull_request, patterns)

        # 3. Improve with feedback
        if developer_accepted:
            self.reinforce_pattern(issues, +1)
        else:
            self.reinforce_pattern(issues, -1)
```

### Advanced: Automatic Bug Fixing System

```python
class AutoBugFixer:
    def __init__(self):
        self.q_agent = QLearningAgent()
        self.memory = VectorMemoryAgent()

    def fix_bug(self, error_log):
        # 1. Classify error
        error_type = classify_error(error_log)

        # 2. Select strategy (Q-learning)
        strategies = self.get_strategies(error_type)
        strategy = self.q_agent.choose_action(error_type, strategies)

        # 3. Reference past experiences
        similar_fixes = self.memory.find_similar(error_log)

        # 4. Attempt fix
        fix = self.generate_fix(strategy, similar_fixes)
        result = self.test_fix(fix)

        # 5. Learn
        reward = 1 if result.passed else -1
        self.q_agent.update(error_type, strategy, reward, ...)
        self.memory.add_experience(error_log, fix, result)
```

---

## Conclusion

Applying reinforcement learning to LLM agents is not just an academic interest but a **practical necessity**.

### Key Takeaways

1. **RLHF**: Standard method for training LLMs themselves
2. **ReAct**: Better reasoning by combining thought and action
3. **Reflexion**: Progressive improvement by learning from failures
4. **Voyager**: Maximize reusability with skill library
5. **In-Context RL**: Adaptation without parameter changes

### Good Starting Point

```
1. Start with simple memory
   → Store experiences in JSON file

2. Add similarity search
   → Find relevant experiences with embeddings

3. Introduce reward system
   → Score success/failure

4. Expand to Q-learning
   → Automatically learn optimal strategy
```

### References

- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Reflexion Paper](https://arxiv.org/abs/2303.11366)
- [Voyager Paper](https://arxiv.org/abs/2305.16291)
- [InstructGPT Paper](https://arxiv.org/abs/2203.02155)
- [Constitutional AI](https://arxiv.org/abs/2212.08073)

---

Build smarter LLM agents with reinforcement learning! 🤖🚀

Feel free to leave questions or suggestions in the comments.
