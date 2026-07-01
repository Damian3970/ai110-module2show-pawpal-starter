# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

    The initial UML design has four classes, one for the owner information, pet information, tasks, and then one to generate a final schedule. For the owner class, there should be basic information such as name, age, and preferences. Likewise, the pet class functions in a similar manner. The task class should describe and manage tasks, and the scheduler class should create a personalized schedule. 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

    Yes, my design changed during implementation. One change that was made was abandoning the idea of noting the owners age (as initially ideated) because I realized that this is not really helpful/relevant for the purpose of this project. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

    The scheduler's main constraints are the available time for the day and the priority that each task has. I knew that the priority of each task mattered most because tasks like giving medicine or feeding to a pet are essential, whereas taking the pet for a walk has a lower priority. In general, constraints that impact the wellbeing of the pet the most are more signficant.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

    One tradeoff the scheduler makes is that it places more emphasis on higher-priority tasks, even if that means less tasks will get done. This tradeoff is reasonable because higher-priority tasks are more essential for the wellbeing of the owner's pets. Therefore, it makes sense to, for example, the owner to take their dog to the vet (1 task), rather than take them on a walk and play with them (2 tasks). 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

    I used AI to brainstorm a UML diagram in the beginning, and later on, design and write tests for the core logic of the app. I found that specific prompts were very helpful, however, at times, open-ended prompts were also helpful. I realized that specific prompts are helpful when you have something particular in mind and need help executing it. On the other hand, open-ended prompts were helpful when tackling unforseen things, for example, such as edge cases. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

    One AI suggestion that I did not accept was during the drafting of the UML diagram. The AI suggested that tasks should belong to the Scheduler rather than the Pet. My reasoning for why I rejected this suggestion was because I thought that the Scheduler doesn't own tasks, but rather, reads the pets' tasks to organize them and output a schedule. I also thought that the Pet owns the tasks. This was my simple logic. 

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

    I wrote tests covering sorting correctness, recurrence logic, conflict detection, scheduling, and filtering. These tests are important because they cover core app logic. Testing them allowed me to reveal bugs and give me the confidence that I needed to ensure that the app runs correctly. 

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

    I am confident that my scheduler works as intended. If I had more time, edge cases that I would look more into include bad inputs, such as negative numbers or empty inputs for example.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

    I am satisfied with the end-result of the app. I like messing around with it.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

    Something I would improve is the UI. I feel like that is kind of lacking in character.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

    One thing that I learned about designing systems as it relates to AI is understanding what type of data each class will possess ownership of. Knowing this early, I believe, will avoid mistakes later down the road.
