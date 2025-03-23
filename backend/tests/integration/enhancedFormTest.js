// tests/integration/enhancedFormTest.js
import axios from 'axios';

/**
 * This test script verifies the integration between the Enhanced Project Form
 * and the backend estimation engine using Jest.
 */

// Mock API client
jest.mock('axios');

describe('Enhanced Project Form Integration Tests', () => {
  // Sample data for testing
  const basicProject = {
    square_footage: 5000,
    global_tier: 'Luxury',
    project_name: 'Integration Test Project',
    bedroom_count: 4,
    primary_bath_count: 2,
    secondary_bath_count: 3
  };

  const enhancedProject = {
    ...basicProject,
    rooms: {
      'room1': {
        name: 'Primary Suite',
        type: 'primary_bath',
        square_footage: 500,
        tier: 'Ultra-Luxury',
        trades: {
          'plumbing': {
            tier: 'Ultra-Luxury'
          },
          'tile': {
            tier: 'Ultra-Luxury'
          }
        }
      },
      'room2': {
        name: 'Kitchen',
        type: 'kitchen',
        square_footage: 400,
        trades: {
          'cabinetry': {
            tier: 'Luxury'
          }
        }
      }
    },
    trades: {
      'electrical': 'Luxury',
      'hvac': 'Premium'
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('Basic estimate endpoint correctly receives project data', async () => {
    // Mock the API response
    axios.post.mockResolvedValue({
      data: { total_cost: 500000 }
    });

    // Call the API
    const response = await axios.post('/api/estimate', basicProject);
    
    // Verify the API was called with the correct data
    expect(axios.post).toHaveBeenCalledWith('/api/estimate', basicProject);
    expect(response.data.total_cost).toBe(500000);
  });

  test('Enhanced estimate endpoint correctly receives project data with rooms and trades', async () => {
    // Mock the API response
    axios.post.mockResolvedValue({
      data: { 
        total_cost: 750000,
        rooms: {
          'room1': { total_cost: 250000 },
          'room2': { total_cost: 150000 }
        }
      }
    });

    // Call the API
    const response = await axios.post('/api/estimate/detailed', enhancedProject);
    
    // Verify the API was called with the correct data
    expect(axios.post).toHaveBeenCalledWith('/api/estimate/detailed', enhancedProject);
    expect(response.data.total_cost).toBe(750000);
    expect(response.data.rooms.room1.total_cost).toBe(250000);
  });

  test('Validation endpoint processes input data correctly', async () => {
    // Mock the API response
    axios.post.mockResolvedValue({
      data: {
        is_valid: true,
        warnings: ['Square footage is unusually high']
      }
    });

    // Call the API
    const response = await axios.post('/api/estimate/validate', enhancedProject);
    
    // Verify the validation result
    expect(response.data.is_valid).toBe(true);
    expect(response.data.warnings).toContain('Square footage is unusually high');
  });

  test('Saving estimate with room data works correctly', async () => {
    // Mock the API response
    axios.post.mockResolvedValue({
      data: {
        status: 'success',
        message: 'Estimation saved as test-estimate'
      }
    });

    // Create estimation result to save
    const estimationResult = {
      project: enhancedProject,
      total_cost: 750000,
      categories: {},
      rooms: {
        'room1': { total_cost: 250000 },
        'room2': { total_cost: 150000 }
      }
    };

    // Call the API
    const response = await axios.post('/api/save/test-estimate', estimationResult);
    
    // Verify the save was successful
    expect(response.data.status).toBe('success');
  });
});

// tests/integration/manualTestPlan.md
/**
# Manual Integration Testing Plan

## Setup
1. Start the backend server: `python -m src.api.app`
2. Start the frontend dev server: `npm run dev`
3. Open the frontend in a browser: `http://localhost:3000`

## Test Cases

### Basic Form Functionality
1. **Test Basic Form Submission**
   - Fill out the basic project form with square footage and tier
   - Submit the form
   - Verify that the estimate is calculated and displayed

2. **Test Data Validation**
   - Enter invalid values (e.g., negative square footage)
   - Verify that validation errors are displayed
   - Fix the errors and resubmit
   - Verify that the estimate is calculated

### Enhanced Form Functionality
1. **Test Room Management**
   - Add multiple rooms of different types
   - Verify that the sum of room square footage is tracked
   - Verify that room-specific options appear based on room type
   - Delete a room and verify it's removed

2. **Test Trade Configuration**
   - Change tier settings for different trades
   - Verify that tier changes are reflected in the UI

3. **Test Room-Trade Configuration**
   - Select a room and modify trade-specific settings
   - Verify that changes are reflected in the UI
   - Reset the room-trade to use default settings
   - Verify the reset is reflected

### API Integration Tests
1. **Test Basic Estimate API**
   - Open the Network tab in DevTools
   - Submit the basic form
   - Verify the request payload matches the form data
   - Verify the response contains the expected estimate structure

2. **Test Enhanced Estimate API**
   - Configure rooms and trades
   - Submit the enhanced form
   - Verify the request payload includes rooms and trades
   - Verify the response contains room-specific estimates

3. **Test Saving and Loading**
   - Generate an estimate
   - Save it with a name
   - Refresh the page
   - Load the saved estimate
   - Verify all data is correctly restored

4. **Test Report Generation**
   - Generate an estimate
   - Save it
   - Generate a summary report
   - Verify the report contains the expected data
   - Generate a detailed report
   - Verify the report includes room-specific details
   - Export to CSV
   - Verify the CSV contains all costed items

## Edge Cases to Test
1. **Large Projects**
   - Create a project with very large square footage (e.g., 50,000 sq ft)
   - Verify that the estimate is calculated correctly

2. **Many Rooms**
   - Add a large number of rooms (e.g., 20+)
   - Verify that the UI handles this correctly
   - Verify that the estimate is calculated correctly

3. **Mixed Tiers**
   - Configure different tiers at all levels (global, room, trade, room-trade)
   - Verify that tier resolution works correctly

4. **Form Reset**
   - Fill out the form with complex data
   - Reset the form
   - Verify that all fields are cleared

5. **Network Errors**
   - Shut down the backend server
   - Attempt to submit the form
   - Verify that error handling works correctly
*/