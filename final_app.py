import streamlit as st
from PIL import Image
import io
import requests

# --- Page Setup ---
st.set_page_config(page_title="Live Image Tool", layout="centered")

# --- Session State Management (The Library) ---
# This keeps images in memory even when you interact with the app
if 'image_library' not in st.session_state:
    st.session_state.image_library = {} # Dictionary to store {filename: image_data}

st.title("⚡ Live Resizer & Compressor")
st.write("Upload multiple images or use a URL. Select one from the library to edit.")

# --- 1. Add Images to Library ---
with st.expander("📂 Add Images to Library", expanded=True):
    tab1, tab2 = st.tabs(["Upload Files", "From URL"])
    
    # Tab 1: Upload Multiple Files
    with tab1:
        uploaded_files = st.file_uploader("Upload images (PNG, JPG, JPEG)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if uploaded_files:
            for upload in uploaded_files:
                # Add to library if not already present
                if upload.name not in st.session_state.image_library:
                    image = Image.open(upload)
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')
                    st.session_state.image_library[upload.name] = image
            st.success(f"Added {len(uploaded_files)} images to the library!")

    # Tab 2: Image URL
    with tab2:
        url_input = st.text_input("Paste Image URL here")
        if st.button("Fetch Image"):
            try:
                response = requests.get(url_input, stream=True)
                response.raise_for_status()
                image = Image.open(response.raw)
                
                # Create a name for URL images
                url_filename = f"url_image_{len(st.session_state.image_library) + 1}.jpg"
                
                if image.mode == 'RGBA':
                    image = image.convert('RGB')
                
                st.session_state.image_library[url_filename] = image
                st.success("Image fetched successfully!")
            except Exception as e:
                st.error(f"Error fetching image: {e}")

# --- 2. Select Image from Library ---
st.write("---")
if not st.session_state.image_library:
    st.info("The library is empty. Please upload an image or use a URL above.")
else:
    # Dropdown to select active image
    image_names = list(st.session_state.image_library.keys())
    selected_name = st.selectbox("Select an image to edit:", image_names)
    
    # Get the selected image object
    original_image = st.session_state.image_library[selected_name]

    # --- 3. Original Stats ---
    st.subheader("1. Original Image Details")
    col1, col2 = st.columns(2)
    with col1:
        st.image(original_image, caption=f"Selected: {selected_name}", use_container_width=True)
    with col2:
        st.metric("Dimensions", f"{original_image.width} x {original_image.height} px")
        # Estimate size in KB (approximation since it's in memory)
        buf_temp = io.BytesIO()
        original_image.save(buf_temp, format="JPEG")
        st.metric("Estimated Size", f"{len(buf_temp.getvalue())/1024:.2f} KB")

    # --- 4. Settings (Live Controls) ---
    st.write("---")
    st.subheader("2. Edit Settings")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Resize Dimensions:**")
        # Use keys to prevent state reloading issues
        new_width = st.number_input("New Width (px)", value=original_image.width, step=10, key="w")
        new_height = st.number_input("New Height (px)", value=original_image.height, step=10, key="h")
        
    with c2:
        st.write("**Compression:**")
        quality = st.slider("Quality (Lower = Smaller Size)", 10, 100, 85, key="q")

    # --- 5. Live Processing ---
    # Resize
    resized_img = original_image.resize((int(new_width), int(new_height)))
    
    # Compress
    buf = io.BytesIO()
    resized_img.save(buf, format="JPEG", quality=quality, optimize=True)
    byte_data = buf.getvalue()
    new_size_kb = len(byte_data) / 1024

    # --- 6. Final Result & Download ---
    st.write("---")
    st.subheader("3. Live Preview & Download")
    
    r1, r2 = st.columns(2)
    with r1:
        st.image(resized_img, caption=f"Result ({new_width}x{new_height})", use_container_width=True)
    with r2:
        st.success(f"New Size: {new_size_kb:.2f} KB")
        
        # Calculate Savings
        original_size_kb = len(buf_temp.getvalue()) / 1024
        savings = original_size_kb - new_size_kb
        if savings > 0:
            st.write(f"✅ You saved **{savings:.2f} KB**!")
        else:
            st.warning("File size increased (likely due to upscaling).")

    # Download Button Logic
    # 1. Clean the original name (remove extension)
    clean_name = selected_name.rsplit('.', 1)[0]
    # 2. Add the requested prefix
    final_filename = f"IMGROR_{clean_name}.jpg"

    st.download_button(
        label=f"⬇️ Download {final_filename}",
        data=byte_data,
        file_name=final_filename,
        mime="image/jpeg",
        type="primary"
    )