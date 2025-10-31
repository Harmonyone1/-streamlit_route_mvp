"""
Script to create sample data Excel file
Run this script to generate sample_data.xlsx with test stops
"""
import pandas as pd
from pathlib import Path

def create_sample_data():
    """Create sample stops data in Excel format"""

    # Sample data for testing
    sample_data = {
        'Name': [
            'ABC Corp',
            'XYZ Industries',
            'Smith Residence',
            'Johnson Office',
            'Downtown Mall',
            'Tech Solutions Inc',
            'Green Park Apartments',
            'City Medical Center',
            'Riverside Hotel',
            'Central Library'
        ],
        'Address': [
            '123 Main St, New York, NY 10001',
            '456 Park Ave, New York, NY 10022',
            '789 Broadway, New York, NY 10003',
            '321 5th Avenue, New York, NY 10016',
            '555 Madison Ave, New York, NY 10022',
            '777 Lexington Ave, New York, NY 10065',
            '888 Amsterdam Ave, New York, NY 10025',
            '999 Central Park West, New York, NY 10025',
            '111 Riverside Drive, New York, NY 10025',
            '222 West 42nd St, New York, NY 10036'
        ],
        'Latitude': [
            40.7589, 40.7614, 40.7338, 40.7452, 40.7614,
            40.7649, 40.7944, 40.7796, 40.7944, 40.7564
        ],
        'Longitude': [
            -73.9851, -73.9776, -73.9910, -73.9820, -73.9776,
            -73.9625, -73.9722, -73.9730, -73.9722, -73.9909
        ],
        'Service Duration': [45, 30, 60, 30, 45, 40, 35, 50, 40, 30],
        'Time Window Start': [
            '09:00', '10:00', '13:00', '09:00', '11:00',
            '10:00', '14:00', '09:00', '10:00', '11:00'
        ],
        'Time Window End': [
            '12:00', '14:00', '17:00', '12:00', '15:00',
            '14:00', '17:00', '12:00', '14:00', '15:00'
        ],
        'Priority': [1, 2, 1, 3, 2, 1, 2, 1, 3, 2],
        'Customer Name': [
            'John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Williams',
            'Charlie Brown', 'David Lee', 'Emma Davis', 'Frank Miller',
            'Grace Wilson', 'Henry Taylor'
        ],
        'Customer Phone': [
            '555-0101', '555-0102', '555-0103', '555-0104', '555-0105',
            '555-0106', '555-0107', '555-0108', '555-0109', '555-0110'
        ],
        'Notes': [
            'Ring doorbell twice',
            'Loading dock in rear',
            'Call on arrival',
            'Suite 401',
            'Meet at entrance',
            'Ask for reception',
            'Building B, Unit 5',
            'Emergency entrance',
            'Front desk check-in required',
            'Reference desk on 2nd floor'
        ]
    }

    # Create DataFrame
    df = pd.DataFrame(sample_data)

    # Ensure data directory exists
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    # Save to Excel with multiple sheets
    output_path = data_dir / 'sample_data.xlsx'

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Stops sheet with data
        df.to_excel(writer, sheet_name='Stops', index=False)

        # Instructions sheet
        instructions = pd.DataFrame({
            'Field': [
                'Name',
                'Address',
                'Latitude',
                'Longitude',
                'Service Duration',
                'Time Window Start',
                'Time Window End',
                'Priority',
                'Customer Name',
                'Customer Phone',
                'Notes'
            ],
            'Description': [
                'Stop name or identifier (REQUIRED)',
                'Full street address (REQUIRED)',
                'Latitude coordinate in decimal degrees',
                'Longitude coordinate in decimal degrees',
                'Service time in minutes (default: 30)',
                'Earliest arrival time in HH:MM format (e.g., 09:00)',
                'Latest arrival time in HH:MM format (e.g., 17:00)',
                'Priority level 1-5 where 1 is highest priority',
                'Customer contact name',
                'Customer phone number',
                'Special instructions or notes for the technician'
            ],
            'Required': [
                'Yes', 'Yes', 'No*', 'No*', 'No',
                'No', 'No', 'No', 'No', 'No', 'No'
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)

    print(f'✅ Sample data file created: {output_path}')
    print(f'📊 Contains {len(df)} sample stops')
    print(f'📋 Includes instructions sheet')
    print('\nYou can now:')
    print('1. Upload this file in the Import/Export page')
    print('2. Use it as a template for your own data')
    print('3. Modify it with your actual stops')

    return output_path

if __name__ == '__main__':
    create_sample_data()
