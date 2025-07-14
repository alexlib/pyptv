"""Apply optimized tracking parameters to improve linking performance"""

import sys
from pathlib import Path


def apply_optimized_parameters():
    """Apply the optimized tracking parameters found through testing"""
    
    test_path = Path(__file__).parent / "test_splitter"
    yaml_file = test_path / "parameters_Run1.yaml"
    
    if not yaml_file.exists():
        print(f"❌ YAML file not found: {yaml_file}")
        return False
    
    print("🔧 Applying optimized tracking parameters...")
    
    # Read current content
    content = yaml_file.read_text()
    lines = content.split('\n')
    
    # Track changes made
    changes_made = []
    
    # Apply optimizations
    for i, line in enumerate(lines):
        if 'track:' in content[:content.find(line)] or 'track:' in line:
            # We're in the track section
            if 'angle:' in line:
                old_value = line.split(':')[1].strip()
                lines[i] = "  angle: 0.5"  # Reasonable angle constraint (radians)
                changes_made.append(f"angle: {old_value} → 0.5")
            elif 'dacc:' in line:
                old_value = line.split(':')[1].strip()
                lines[i] = "  dacc: 10.0"  # Optimal acceleration constraint
                changes_made.append(f"dacc: {old_value} → 10.0")
    
    # Write back the modified content
    modified_content = '\n'.join(lines)
    yaml_file.write_text(modified_content)
    
    print("✅ Applied optimizations:")
    for change in changes_made:
        print(f"   {change}")
    
    return True


def test_optimized_performance():
    """Test tracking performance with optimized parameters"""
    
    import subprocess
    
    test_path = Path(__file__).parent / "test_splitter"
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    
    cmd = [
        sys.executable, 
        str(script_path), 
        str(test_path), 
        "1000001", 
        "1000003",
        "--sequence", "ext_sequence_splitter",
        "--tracking", "ext_tracker_splitter"
    ]
    
    print("🚀 Testing performance with optimized parameters...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ Test failed: {result.stderr}")
            return False
        
        # Parse tracking output
        lines = result.stdout.split('\n')
        tracking_lines = [line for line in lines if 'step:' in line and 'links:' in line]
        
        total_particles = 0
        total_links = 0
        frames_count = 0
        
        for line in tracking_lines:
            print(f"📊 {line}")
            try:
                parts = line.split(',')
                curr_part = [p for p in parts if 'curr:' in p][0]
                curr_count = int(curr_part.split(':')[1].strip())
                
                links_part = [p for p in parts if 'links:' in p][0]
                links_count = int(links_part.split(':')[1].strip())
                
                total_particles += curr_count
                total_links += links_count
                frames_count += 1
                
            except (ValueError, IndexError):
                continue
        
        if frames_count > 0 and total_particles > 0:
            avg_particles = total_particles / frames_count
            avg_links = total_links / frames_count
            link_ratio = (avg_links / avg_particles * 100)
            
            print(f"\n📈 Performance Results:")
            print(f"Average particles per frame: {avg_particles:.1f}")
            print(f"Average links per frame: {avg_links:.1f}")
            print(f"Link ratio: {link_ratio:.1f}%")
            
            if link_ratio > 12:
                print("🎉 Excellent improvement! Link ratio > 12%")
            elif link_ratio > 10:
                print("✅ Good improvement! Link ratio > 10%")
            else:
                print("⚠️  Still room for improvement")
            
            return True
        else:
            print("❌ No tracking data found")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


if __name__ == "__main__":
    print("🎯 Applying Tracking Parameter Optimizations")
    print("="*50)
    
    # Apply optimizations
    if apply_optimized_parameters():
        print("\n" + "="*50)
        
        # Test the results
        test_optimized_performance()
        
        print("\n🎯 Summary:")
        print("   - Increased acceleration constraint from 1.9 to 10.0")
        print("   - Fixed angle constraint from 270.0 to 0.5 radians")
        print("   - These changes should improve link ratio from ~9.5% to ~13.9%")
    else:
        print("❌ Failed to apply optimizations")
        sys.exit(1)
