# Budget Calculator Backend

Welcome to the backend of the Budget Calculator project. This component is responsible for processing project data, performing cost estimations, and serving the results to the frontend interface.

## Overview

The backend is structured to ensure modularity, clarity, and adaptability. It comprises several key directories and files:

- **`src/api/`**: Manages API endpoints for handling client requests.
- **`src/core/`**: Contains the core logic for processing and estimating project costs.
- **`src/utils/`**: Houses reusable helper functions utilized across the backend.
- **`data/catalog.csv`**: Serves as the primary data source for material and labor costs.
- **`config/`**: Contains configuration files allowing adjustments to cost parameters.

## Current Status

We are actively refining the backend to enhance its functionality and maintainability:

- **Estimator Modules**: Ensuring all modules operate correctly and return accurate estimates.
- **Documentation**: Adding comprehensive comments and documentation for better code understanding.
- **Config Integration**: Validating that cost adjustments can be made seamlessly through the `config/` files.
- **Pricing Integration**: Currently working on connecting cost tie-ins with the enhanced catalog.


## Running the Estimation Code

To test the backend estimation engine, run the following command:

```sh
python main.py --input tests/sample_project.json --output sample_results.json --report sample_report.txt --csv sample_csv.csv --estimator_report sample_estimator_report.txt
```

## Pricing Integration

Please note that we are still in the process of integrating dynamic pricing tie-ins. This will enable real-time cost updates based on current market rates, ensuring more accurate and up-to-date estimations.

## Development Guidelines

To maintain consistency and quality, please adhere to the following guidelines:

1. **Path Naming Conventions**: Use clear and descriptive names for all modules and files.
2. **Code Documentation**: Include docstrings and inline comments for all functions and modules.
3. **Modularity**: Design estimator modules to be independent and self-contained.
4. **Config-Driven Design**: Ensure cost adjustments are configurable via JSON files in the `config/` directory.

## Testing

Comprehensive testing is crucial for reliability:

- **Backend Tests (`backend/tests/`)**: Verify that estimators return expected values and API endpoints respond correctly.
- **Frontend Tests (`frontend/cypress/e2e/`)**: Ensure UI forms process data correctly and estimation results display properly.

## Contributing

We welcome contributions! Please ensure that any code changes are accompanied by appropriate tests and documentation. For major changes, open an issue first to discuss your proposed modifications.

---

Thank you for your interest in the Budget Calculator project. Together, we can build a tool that provides accurate and efficient budget estimations for a variety of projects.
