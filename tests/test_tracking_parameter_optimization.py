"""Test different tracking parameter values to improve link ratio"""

import subprocess
import sys
import tempfile
import shutil
import yaml
from pathlib import Path


def test_tracking_with_different_parameters():
    """Test tracking with progressively more relaxed velocity constraints"""
    
    base_test_path = Path(__file__).parent / "test_splitter"
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    
    if not base_test_path.exists() or not script_path.exists():
        print("❌ Required files not found")
        return
    
    # Different parameter sets to test
    parameter_sets = [
        {
            'name': 'Current (±1.9)',
            'dvxmin': -1.9, 'dvxmax': 1.9,
            'dvymin': -1.9, 'dvymax': 1.9,
            'dvzmin': -1.9, 'dvzmax': 1.9
        },
        {
            'name': 'Relaxed (±3.0)',
            'dvxmin': -3.0, 'dvxmax': 3.0,
            'dvymin': -3.0, 'dvymax': 3.0,
            'dvzmin': -3.0, 'dvzmax': 3.0
        },
        {
            'name': 'Very Relaxed (±5.0)',
            'dvxmin': -5.0, 'dvxmax': 5.0,
            'dvymin': -5.0, 'dvymax': 5.0,
            'dvzmin': -5.0, 'dvzmax': 5.0
        },
        {
            'name': 'Extremely Relaxed (±10.0)',
            'dvxmin': -10.0, 'dvxmax': 10.0,
            'dvymin': -10.0, 'dvymax': 10.0,
            'dvzmin': -10.0, 'dvzmax': 10.0
        }
    ]
    
    results = []
    
    for param_set in parameter_sets:
        print(f"\n🧪 Testing {param_set['name']}")
        print("="*50)
        
        # Create temporary test directory with modified parameters
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_test_path = Path(temp_dir) / "test_splitter"
            shutil.copytree(base_test_path, temp_test_path)
            
            # Modify YAML parameters
            yaml_file = temp_test_path / "parameters_Run1.yaml"
            
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Update tracking parameters
            if 'track' not in data:
                data['track'] = {}
            
            for key in ['dvxmin', 'dvxmax', 'dvymin', 'dvymax', 'dvzmin', 'dvzmax']:
                data['track'][key] = param_set[key]
            
            with open(yaml_file, 'w') as f:
                yaml.safe_dump(data, f)
            
            # Run tracking test
            cmd = [
                sys.executable, 
                str(script_path), 
                str(temp_test_path), 
                "1000001", 
                "1000002",  # Just 2 frames for speed
                "--sequence", "ext_sequence_splitter",
                "--tracking", "ext_tracker_splitter"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    # Parse tracking results
                    links_info = parse_tracking_output(result.stdout)
                    results.append({
                        'name': param_set['name'],
                        'parameters': param_set,
                        'results': links_info
                    })
                    
                    if links_info:
                        avg_links = sum(info['links'] for info in links_info) / len(links_info)
                        avg_particles = sum(info['curr'] for info in links_info) / len(links_info)
                        link_ratio = (avg_links / avg_particles * 100) if avg_particles > 0 else 0
                        
                        print(f"✅ Average links: {avg_links:.1f}")
                        print(f"✅ Average particles: {avg_particles:.1f}")
                        print(f"✅ Link ratio: {link_ratio:.1f}%")
                    else:
                        print("❌ No tracking output found")
                else:
                    print(f"❌ Run failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("❌ Run timed out")
    
    # Summary comparison
    print("\n📊 Parameter Comparison Summary:")
    print("="*60)
    print(f"{'Parameter Set':<20} {'Link Ratio':<12} {'Avg Links':<10} {'Avg Particles':<12}")
    print("-"*60)
    
    for result in results:
        if result['results']:
            links_info = result['results']
            avg_links = sum(info['links'] for info in links_info) / len(links_info)
            avg_particles = sum(info['curr'] for info in links_info) / len(links_info)
            link_ratio = (avg_links / avg_particles * 100) if avg_particles > 0 else 0
            
            print(f"{result['name']:<20} {link_ratio:<12.1f}% {avg_links:<10.1f} {avg_particles:<12.1f}")
    
    # Find best performing parameters
    best_result = None
    best_ratio = 0
    
    for result in results:
        if result['results']:
            links_info = result['results']
            avg_links = sum(info['links'] for info in links_info) / len(links_info)
            avg_particles = sum(info['curr'] for info in links_info) / len(links_info)
            link_ratio = (avg_links / avg_particles * 100) if avg_particles > 0 else 0
            
            if link_ratio > best_ratio:
                best_ratio = link_ratio
                best_result = result
    
    if best_result:
        print(f"\n🏆 Best performing parameters: {best_result['name']}")
        print(f"🏆 Best link ratio: {best_ratio:.1f}%")
        print("🏆 Recommended parameters:")
        for key, value in best_result['parameters'].items():
            if key != 'name':
                print(f"   {key}: {value}")


def parse_tracking_output(output_text):
    """Parse tracking output to extract link statistics"""
    lines = output_text.split('\n')
    tracking_lines = [line for line in lines if 'step:' in line and 'links:' in line]
    
    results = []
    for line in tracking_lines:
        try:
            parts = line.split(',')
            curr_part = [p for p in parts if 'curr:' in p][0]
            curr_count = int(curr_part.split(':')[1].strip())
            
            links_part = [p for p in parts if 'links:' in p][0]
            links_count = int(links_part.split(':')[1].strip())
            
            lost_part = [p for p in parts if 'lost:' in p][0]
            lost_count = int(lost_part.split(':')[1].strip())
            
            results.append({
                'curr': curr_count,
                'links': links_count,
                'lost': lost_count
            })
        except (ValueError, IndexError):
            continue
    
    return results


if __name__ == "__main__":
    test_tracking_with_different_parameters()
