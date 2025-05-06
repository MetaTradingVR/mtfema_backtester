                filtered_data = self.data[visible_columns]
            else:  # List of dicts
                filtered_data = []
                for row in self.data:
                    filtered_row = {col: row.get(col, '') for col in visible_columns}
                    filtered_data.append(filtered_row)
            
            # Handle pagination
            if pagination and len(filtered_data) > page_size:
                page_number = st.select_slider(
                    f"Page ({len(filtered_data)} items total)",
                    options=range(1, (len(filtered_data) // page_size) + 2),
                    value=1
                )
                
                start_idx = (page_number - 1) * page_size
                end_idx = min(start_idx + page_size, len(filtered_data))
                
                if hasattr(filtered_data, 'iloc'):  # pandas DataFrame
                    paginated_data = filtered_data.iloc[start_idx:end_idx]
                else:  # List of dicts
                    paginated_data = filtered_data[start_idx:end_idx]
            else:
                paginated_data = filtered_data
            
            # Display table
            st.dataframe(paginated_data, use_container_width=True)
            
            return paginated_data
        else:
            # Non-Streamlit implementation would go here
            logger.warning("Streamlit not available, table rendering skipped")
            return None


class ResponsiveForm(ResponsiveComponent):
    """
    Responsive form component that adapts to different screen sizes.
    
    Features:
    - Automatic layout changes based on screen size
    - Input field sizing for mobile
    - Validation suited for touch interfaces
    - Simplified options on mobile
    """
    
    def __init__(self, 
                component_id: str, 
                title: str = "",
                description: str = ""):
        """
        Initialize a responsive form component.
        
        Args:
            component_id: Unique identifier for the component
            title: Title for the form
            description: Description for the form
        """
        super().__init__(component_id, title, description)
        
        # Form fields configuration
        self.fields = []
        self.field_values = {}
        self.validation_errors = {}
        
        # Set default properties for different devices
        self.set_device_property(DeviceType.DESKTOP, "layout", "horizontal")
        self.set_device_property(DeviceType.DESKTOP, "show_advanced", True)
        
        self.set_device_property(DeviceType.TABLET, "layout", "vertical")
        self.set_device_property(DeviceType.TABLET, "show_advanced", True)
        
        self.set_device_property(DeviceType.MOBILE, "layout", "vertical")
        self.set_device_property(DeviceType.MOBILE, "show_advanced", False)
        
        self.set_device_property(DeviceType.MOBILE_SMALL, "layout", "vertical")
        self.set_device_property(DeviceType.MOBILE_SMALL, "show_advanced", False)
        
        # Callbacks
        self.submit_callback = None
    
    def add_field(self, 
                field_id: str, 
                label: str, 
                field_type: str, 
                default_value: Any = None,
                options: List[Any] = None,
                required: bool = False,
                advanced: bool = False,
                help_text: str = ""):
        """
        Add a field to the form.
        
        Args:
            field_id: Unique identifier for the field
            label: Display label for the field
            field_type: Type of field (text, number, select, checkbox, etc.)
            default_value: Default value for the field
            options: Options for select fields
            required: Whether the field is required
            advanced: Whether this is an advanced field (may be hidden on mobile)
            help_text: Help text to display with the field
        """
        field = {
            "id": field_id,
            "label": label,
            "type": field_type,
            "default": default_value,
            "options": options,
            "required": required,
            "advanced": advanced,
            "help_text": help_text
        }
        
        self.fields.append(field)
        self.field_values[field_id] = default_value
    
    def set_submit_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set callback function for form submission.
        
        Args:
            callback: Function to call with form values when submitted
        """
        self.submit_callback = callback
    
    def validate_field(self, field_id: str, value: Any) -> Optional[str]:
        """
        Validate a field value.
        
        Args:
            field_id: ID of the field to validate
            value: Value to validate
            
        Returns:
            Error message if validation fails, None otherwise
        """
        # Find field configuration
        field = next((f for f in self.fields if f["id"] == field_id), None)
        if not field:
            return None
            
        # Check required fields
        if field["required"] and (value is None or value == ""):
            return f"{field['label']} is required"
            
        # Type-specific validation
        if field["type"] == "email" and value:
            # Simple email validation
            if "@" not in value or "." not in value:
                return "Please enter a valid email address"
                
        elif field["type"] == "number" and value:
            # Validate number
            try:
                float(value)
            except ValueError:
                return "Please enter a valid number"
                
        # Add more validation as needed
        
        return None
    
    def validate_form(self) -> bool:
        """
        Validate all form fields.
        
        Returns:
            Whether the form is valid
        """
        self.validation_errors = {}
        
        for field in self.fields:
            field_id = field["id"]
            value = self.field_values.get(field_id)
            
            error = self.validate_field(field_id, value)
            if error:
                self.validation_errors[field_id] = error
        
        return len(self.validation_errors) == 0
    
    def render(self, screen_width: int) -> Optional[Any]:
        """
        Render the form based on screen size.
        
        Args:
            screen_width: Width of the screen in pixels
            
        Returns:
            Rendered form or None
        """
        if not self.is_visible:
            return None
            
        device_type = self.detect_device_type(screen_width)
        
        # Get device-specific properties
        layout = self.get_property("layout", device_type, "vertical")
        show_advanced = self.get_property("show_advanced", device_type, True)
        
        # Check if we're using Streamlit
        if HAS_STREAMLIT:
            st.subheader(self.title)
            if self.description:
                st.write(self.description)
            
            with st.form(self.component_id):
                # Render fields
                for field in self.fields:
                    # Skip advanced fields on mobile if configured
                    if field["advanced"] and not show_advanced:
                        continue
                    
                    field_id = field["id"]
                    
                    # Use columns for horizontal layout
                    if layout == "horizontal":
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.write(f"{field['label']}:")
                        with col2:
                            self._render_field(field, device_type)
                    else:
                        st.write(f"{field['label']}:")
                        self._render_field(field, device_type)
                    
                    # Show error if any
                    if field_id in self.validation_errors:
                        st.error(self.validation_errors[field_id])
                
                # Submit button
                submitted = st.form_submit_button("Submit")
                
                if submitted:
                    if self.validate_form():
                        if self.submit_callback:
                            self.submit_callback(self.field_values)
                    else:
                        st.error("Please fix the errors in the form")
            
            return self.field_values
        else:
            # Non-Streamlit implementation would go here
            logger.warning("Streamlit not available, form rendering skipped")
            return None
    
    def _render_field(self, field: Dict[str, Any], device_type: DeviceType) -> None:
        """Render a specific form field based on type."""
        field_id = field["id"]
        current_value = self.field_values.get(field_id, field["default"])
        
        # Adjust field properties based on device
        field_width = "100%"  # Default width
        
        if field["type"] == "text":
            self.field_values[field_id] = st.text_input(
                label="",
                value=current_value or "",
                help=field["help_text"],
                key=f"{self.component_id}_{field_id}"
            )
        
        elif field["type"] == "number":
            self.field_values[field_id] = st.number_input(
                label="",
                value=float(current_value) if current_value is not None else 0,
                help=field["help_text"],
                key=f"{self.component_id}_{field_id}"
            )
        
        elif field["type"] == "select":
            self.field_values[field_id] = st.selectbox(
                label="",
                options=field["options"] or [],
                index=field["options"].index(current_value) if current_value in field["options"] else 0,
                help=field["help_text"],
                key=f"{self.component_id}_{field_id}"
            )
        
        elif field["type"] == "checkbox":
            self.field_values[field_id] = st.checkbox(
                label="",
                value=bool(current_value),
                help=field["help_text"],
                key=f"{self.component_id}_{field_id}"
            )
        
        elif field["type"] == "radio":
            self.field_values[field_id] = st.radio(
                label="",
                options=field["options"] or [],
                index=field["options"].index(current_value) if current_value in field["options"] else 0,
                help=field["help_text"],
                key=f"{self.component_id}_{field_id}"
            )
        
        elif field["type"] == "textarea":
            self.field_values[field_id] = st.text_area(
                label="",
                value=current_value or "",
                help=field["help_text"],
                key=f"{self.component_id}_{field_id}"
            )
        
        elif field["type"] == "date":
            self.field_values[field_id] = st.date_input(
                label="",
                value=current_value,
                help=field["help_text"],
                key=f"{self.component_id}_{field_id}"
            )
        
        # Add more field types as needed


class ResponsiveLayout:
    """
    Manages overall layout of responsive components.
    
    Features:
    - Global layout configuration
    - Component organization
    - Device detection
    - Style consistency
    """
    
    def __init__(self, title: str = "MT 9 EMA Backtester"):
        """
        Initialize a responsive layout.
        
        Args:
            title: Title for the application
        """
        self.title = title
        self.components = {}
        self.component_order = []
        self.global_styles = {}
        
        # Cache for last detected device type
        self.last_device_type = None
        self.last_screen_width = None
    
    def add_component(self, 
                     component: ResponsiveComponent, 
                     position: Optional[int] = None) -> None:
        """
        Add a component to the layout.
        
        Args:
            component: Component to add
            position: Optional position in the order (None = append)
        """
        component_id = component.component_id
        self.components[component_id] = component
        
        # Update order
        if component_id not in self.component_order:
            if position is None or position >= len(self.component_order):
                self.component_order.append(component_id)
            else:
                self.component_order.insert(position, component_id)
    
    def remove_component(self, component_id: str) -> bool:
        """
        Remove a component from the layout.
        
        Args:
            component_id: ID of the component to remove
            
        Returns:
            Whether the component was found and removed
        """
        if component_id in self.components:
            del self.components[component_id]
            self.component_order.remove(component_id)
            return True
        return False
    
    def get_component(self, component_id: str) -> Optional[ResponsiveComponent]:
        """
        Get a component by ID.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Component if found, None otherwise
        """
        return self.components.get(component_id)
    
    def set_global_style(self, style_property: str, value: str) -> None:
        """
        Set a global style for the layout.
        
        Args:
            style_property: CSS property name
            value: CSS property value
        """
        self.global_styles[style_property] = value
    
    def render(self, screen_width: int) -> None:
        """
        Render all components in the layout.
        
        Args:
            screen_width: Width of the screen in pixels
        """
        # Detect device type for reference
        self.last_screen_width = screen_width
        self.last_device_type = ResponsiveComponent().detect_device_type(screen_width)
        
        # Check if we're using Streamlit
        if HAS_STREAMLIT:
            st.title(self.title)
            
            # Apply global styles
            if self.global_styles:
                style_str = "; ".join([f"{k}: {v}" for k, v in self.global_styles.items()])
                st.markdown(f"<style>{style_str}</style>", unsafe_allow_html=True)
            
            # Render components in order
            for component_id in self.component_order:
                component = self.components.get(component_id)
                if component:
                    component.render(screen_width)
        else:
            # Non-Streamlit implementation would go here
            logger.warning("Streamlit not available, layout rendering skipped")


# Helper functions for easier access

def create_responsive_chart(component_id: str, title: str = "", description: str = "") -> ResponsiveChart:
    """
    Create a responsive chart component.
    
    Args:
        component_id: Unique identifier for the component
        title: Title for the chart
        description: Description for the chart
        
    Returns:
        Responsive chart component
    """
    return ResponsiveChart(component_id, title, description)

def create_responsive_table(component_id: str, title: str = "", description: str = "") -> ResponsiveTable:
    """
    Create a responsive table component.
    
    Args:
        component_id: Unique identifier for the component
        title: Title for the table
        description: Description for the table
        
    Returns:
        Responsive table component
    """
    return ResponsiveTable(component_id, title, description)

def create_responsive_form(component_id: str, title: str = "", description: str = "") -> ResponsiveForm:
    """
    Create a responsive form component.
    
    Args:
        component_id: Unique identifier for the component
        title: Title for the form
        description: Description for the form
        
    Returns:
        Responsive form component
    """
    return ResponsiveForm(component_id, title, description)

def create_responsive_layout(title: str = "MT 9 EMA Backtester") -> ResponsiveLayout:
    """
    Create a responsive layout.
    
    Args:
        title: Title for the application
        
    Returns:
        Responsive layout
    """
    return ResponsiveLayout(title)
