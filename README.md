# SME Finance AI Agent


![Repo size](https://img.shields.io/github/repo-size/pablo-reyes8/sme-financial-ai-agent)
![Last commit](https://img.shields.io/github/last-commit/pablo-reyes8/sme-financial-ai-agent)
![Open issues](https://img.shields.io/github/issues/pablo-reyes8/sme-financial-ai-agent)
![Contributors](https://img.shields.io/github/contributors/pablo-reyes8/sme-financial-ai-agent)
![Forks](https://img.shields.io/github/forks/pablo-reyes8/sme-financial-ai-agent?style=social)
![Stars](https://img.shields.io/github/stars/pablo-reyes8/sme-financial-ai-agent?style=social)




An AI-driven chatbot built with Flask and LangChain to provide Colombian SMEs with practical financial guidance. It ingests live government-published documents (DIAN, MinCIT, CCB), chunks them, embeds with OpenAI, and retrieves threshold-filtered answers on cash flow, taxes, financing and more.

## Features

- **Live Document Ingestion**  
  Automatically scrapes and parses official pages to keep regulations and tax codes up to date.  
- **Semantic Retrieval**  
  Uses OpenAI embeddings stored in ChromaDB and a CustomThresholdRetriever to surface only highly relevant chunks.  
- **Structured Advisory Protocol**  
  Enforces multi-section responses (intro, recommended steps, risks/points of attention, optional timeline, closing) via a tailored prompt template.  
- **Interactive Web UI**  
  Responsive Flask interface with session memory, quick-reply buttons, dark-mode toggle and typing indicator for a smooth user experience.

## Tech Stack

- **Language:** Python 3.10+  
- **Web:** Flask, Jinja2 templates, Requests, BeautifulSoup  
- **AI/ML:** LangChain, ChromaDB, OpenAI Embeddings, ConversationalRetrievalChain  
- **Configuration:** dotenv for environment variables  

## Configuration & Usage

1. Define environment variables (e.g. `OPENAI_API_KEY`) in a `.env` file or your shell.  
2. Launch the Flask app and navigate to `http://localhost:5000`.  
3. Ask any finance-related question for SMEs in Colombia and receive structured, actionable advice.

## API Reference

| Endpoint | Method | Description                                |
|:--------:|:------:|--------------------------------------------|
| `/`      | GET    | Load the chat interface                    |
| `/`      | POST   | Submit user query, return AI-generated reply |

## Next Steps

- Schedule automated re-scraping and vectorstore refresh to capture regulatory updates.  
- Extend support to regional tax regimes, export compliance and payroll modules.  
- Add user authentication and personalized dashboards for multi-user scenarios.

## Contributing

Contributions are welcome! Please open issues or submit pull requests at  
https://github.com/pablo-reyes8

## License

This project is licensed under the Apache License 2.0.  

