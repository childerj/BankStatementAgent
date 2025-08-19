# Bank Statement Processing Azure Function

An Azure Function that automatically processes bank statement PDFs uploaded to Azure Blob Storage, extracts data using Azure AI Document Intelligence, and generates BAI2 files for bank reconciliation.

## Features

- **Automated Processing**: EventGrid-triggered processing when PDFs are uploaded
- **AI-Powered Extraction**: Uses Azure Document Intelligence prebuilt bank statement model
- **Multiple File Formats**: Supports both digital and scanned PDFs
- **Fallback Processing**: Falls back to OCR layout analysis if bank statement model fails
- **File Organization**: Automatically organizes files into folders (incoming, processed, archive)
- **BAI2 Generation**: Creates BAI2 format files for bank reconciliation
- **Reconciliation Logic**: Includes transaction reconciliation and summary reporting
- **Clean Logging**: ASCII-only output with "Working Copy" labels

## Architecture

```
Azure Blob Storage (bank-reconciliation container)
├── incoming-bank-statements/     # Upload PDFs here
├── bai2-outputs/                # Generated BAI2 files
└── archive/                     # Processed PDFs

Azure Function App (BankStatementAgent)
├── EventGrid Trigger            # Monitors blob uploads
├── Document Intelligence        # AI extraction
└── Application Insights         # Logging and monitoring
```

## Setup

### Prerequisites
- Azure subscription
- Azure Storage Account
- Azure Document Intelligence service
- Azure Function App (Python 3.12)
- EventGrid subscription for blob storage events

### Environment Variables
```
STORAGE_ACCOUNT_NAME=your-storage-account
STORAGE_ACCOUNT_KEY=your-storage-key
DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-service.cognitiveservices.azure.com/
DOCUMENT_INTELLIGENCE_KEY=your-document-intelligence-key
APPINSIGHTS_INSTRUMENTATIONKEY=your-app-insights-key
```

### Local Development
1. Clone this repository
2. Create virtual environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `local.settings.json.example` to `local.settings.json` and configure
6. Run locally: `func host start`

### Azure Deployment
```bash
func azure functionapp publish BankStatementAgent --python
```

## Usage

1. **Upload PDF**: Drop bank statement PDF into `incoming-bank-statements/` folder
2. **Automatic Processing**: Function triggers within 1-3 minutes via EventGrid
3. **Monitor Logs**: Check Application Insights for processing status
4. **Retrieve Results**: Find BAI2 file in `bai2-outputs/` and archived PDF in `archive/`

## Monitoring

- **Application Insights**: Real-time logs and performance metrics
- **Azure Portal**: Function execution history and health
- **Storage Explorer**: Monitor file processing status

## File Structure

- `function_app.py` - Main Azure Function logic
- `requirements.txt` - Python dependencies
- `host.json` - Function host configuration
- `local.settings.json` - Local development settings
- `test_*.py` - Test scripts for local development
- `*.ps1` - PowerShell utilities and monitoring scripts

## Technologies Used

- **Azure Functions** (Python 3.12)
- **Azure Blob Storage** (EventGrid triggers)
- **Azure AI Document Intelligence** (Bank statement model + OCR fallback)
- **Azure Application Insights** (Logging and monitoring)
- **Python Libraries**: azure-functions, azure-storage-blob, azure-ai-documentintelligence

## Version History

- **v1.0** - Initial release with basic PDF processing
- **v2.0** - Added AI extraction with Document Intelligence
- **v3.0** - EventGrid triggers, proper folder structure, reconciliation logic
- **v4.0** - Improved error handling, ASCII logging, "Working Copy" labels

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Deploy to staging environment
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
