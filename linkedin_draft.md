**Headline: Why I built my own finance tracker (that actually understands receipts)**

I’ve tried a dozen personal finance apps. They all eventually fail for the same reason: **friction**.

The moment I have to unlock my phone, find the app, click "add transaction", select a category, and type in the amount... I’ve already lost interest. It’s too much work for a simple coffee.

So I built a tool that actually fits into my daily flow. It’s a Telegram bot that removes all the manual admin.

Here is how I use it:
📸 **Visual Tracking:** I just snap a picture of my receipt. The bot reads the image, extracts the total, figures out the category (e.g., "Groceries"), and logs it automatically.
🎤 **Voice Notes:** I send a quick audio message on the go: *"Charged 20k to the subway card and spent 5000 on breakfast."* It transcribes the audio, understands the context, and logs it.
🧠 **Model Flexibility:** I’m currently running it on **Gemini 2.0 Flash** because it’s incredibly fast and cost-efficient, but the system is designed to allow swapping models easily.
🇦🇷 **Native Spanish Context:** Built for my daily use in Argentina, the prompts are optimized for Spanish and local slang (though easily adaptable).

**Why PocketFlow? (vs LangChain/CrewAI)**
I skipped the massive agentic frameworks intentionally. For a tool this specific, I found them too abstract—too much "magic" happening behind the scenes.
I used **PocketFlow** because I wanted absolute clarity. It lets me organize logic into independent Nodes (Flow-based programming) with completely decoupled prompts. If a step fails, I know exactly where and why. No hidden chains, just clean, debuggable logic.

Everything logs to my own Google Sheet. I own the data.

It’s not perfect, but it’s the first time I’ve actually stuck to a tracking habit for more than a month. Complexity kills consistency, so I optimized for laziness.

#Python #GeminiAI #PocketFlow #FinTech #BuildInPublic
