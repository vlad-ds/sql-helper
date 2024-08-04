import streamlit as st
import re
import json

def extract_jinja_variables(query, existing_params):
    regex = r'\{\{\s*([\w.]+)\s*\}\}'
    variables = {}
    for match in re.finditer(regex, query):
        full_path = match.group(1)
        parts = full_path.split('.')
        
        # Check if the variable exists in existing_params
        current_param_obj = existing_params
        is_in_params = True
        for part in parts:
            if isinstance(current_param_obj, dict) and part in current_param_obj:
                current_param_obj = current_param_obj[part]
            else:
                is_in_params = False
                break
        
        # If not in existing_params, add to variables
        if not is_in_params:
            current_obj = variables
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    if part not in current_obj:
                        current_obj[part] = ''
                else:
                    current_obj[part] = current_obj.get(part, {})
                    current_obj = current_obj[part]
    
    return variables

def render_query(query, variables, parsed_variables):
    rendered = query
    
    def replace_variable(obj, prefix=''):
        nonlocal rendered
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                replace_variable(value, full_key)
            else:
                regex = re.compile(r'\{\{\s*' + re.escape(full_key) + r'\s*\}\}')
                rendered = regex.sub(str(value), rendered)
    
    # Replace variables from parsed_variables first
    replace_variable(parsed_variables)
    
    # Then replace variables from custom variables
    replace_variable(variables)
    
    # Handle any remaining unresolved variables
    unresolved_regex = r'\{\{\s*([\w.]+)\s*\}\}'
    rendered = re.sub(unresolved_regex, lambda m: f"[Unresolved: {m.group(1)}]", rendered)
    
    return rendered

def main():
    st.title("SQL Query Editor with Jinja Variable Rendering")

    # Create two columns
    col1, col2 = st.columns([0.8, 0.2])

    with col1:
        # SQL Query Input
        st.subheader("SQL Query")
        sql_query = st.text_area("SQL Query (with Jinja variables)", 
                                 height=300, 
                                 placeholder="Enter your SQL query here. Use {{ variable_name }} or {{ object.property }} for Jinja variables.")

        # Parameters Input
        # Parameters parent input
        params_parent = st.text_input("Parameters parent", 
                                    placeholder="Enter parent object for parameters or leave blank for top-level parameters")
        params_input = st.text_area("Paste Python-style Parameters", 
                                    height=100, 
                                    placeholder='Example: {"entity": "italy", "date": 2032}')

        # Parse Parameters
        if st.button("Parse Parameters"):
            try:
                parsed_params = json.loads(params_input.replace("'", '"'))
                st.session_state['parsed_params'] = parsed_params
                st.session_state['params_parent'] = params_parent
                st.success("Parameters parsed successfully!")
            except json.JSONDecodeError:
                st.error("Error parsing parameters. Please check your input format.")

        # Render Query Button
        render_button = st.button("Render Query")

    with col2:
        st.subheader("Variables")
        # Extract and display Jinja variables
        parsed_params = st.session_state.get('parsed_params', {})
        params_parent = st.session_state.get('params_parent')
        jinja_vars = extract_jinja_variables(sql_query, parsed_params)

        # Combine parsed parameters and custom variables
        # if params_parent:
        #     all_variables = {params_parent: parsed_params, **jinja_vars}
        # else:
        #     all_variables = {**parsed_params, **jinja_vars}

        if params_parent:
            parsed_variables = {params_parent: parsed_params}
        else:
            parsed_variables = parsed_params

        for key, value in parsed_variables.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    updated_value = st.text_input(f"{key}.{sub_key}", value=sub_value, key=f"{key}.{sub_key}", disabled=True)
                    if key not in parsed_variables:
                        parsed_variables[key] = {}
                    parsed_variables[key][sub_key] = updated_value
            else:
                updated_value = st.text_input(key, value=value, key=key, disabled=True)
                parsed_variables[key] = updated_value

        # Display and edit variables
        updated_variables = {}
        for key, value in jinja_vars.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    updated_value = st.text_input(f"{key}.{sub_key}", value=sub_value, key=f"{key}.{sub_key}")
                    if key not in updated_variables:
                        updated_variables[key] = {}
                    updated_variables[key][sub_key] = updated_value
            else:
                updated_value = st.text_input(key, value=value, key=key)
                updated_variables[key] = updated_value

    # Render Query (outside of columns to use full width)
    if render_button:
        rendered_query = render_query(sql_query, updated_variables, parsed_variables)
        st.subheader("Rendered Query")
        st.text_area("", value=rendered_query, height=200)

if __name__ == "__main__":
    main()