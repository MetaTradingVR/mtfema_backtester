        with settings_tabs[1]:
            st.markdown("### Data Settings")
            
            # Data cache
            st.checkbox("Enable data caching", value=True)
            cache_dir = st.text_input("Cache Directory", value="./data/cache")
            
            # Data sources
            st.subheader("Data Sources")
            
            # Add Yahoo Finance API settings
            st.markdown("#### Yahoo Finance")
            st.checkbox("Enable Yahoo Finance API", value=True)
            
            # Add Alpha Vantage API settings
            st.markdown("#### Alpha Vantage")
            st.checkbox("Enable Alpha Vantage API", value=False)
            alpha_vantage_key = st.text_input("Alpha Vantage API Key", type="password")
            
            # Add Tradovate API settings
            st.markdown("#### Tradovate")
            st.checkbox("Enable Tradovate API", value=False)
            tradovate_user = st.text_input("Tradovate Username")
            tradovate_password = st.text_input("Tradovate Password", type="password")
            tradovate_app_id = st.text_input("Tradovate App ID")
            tradovate_app_secret = st.text_input("Tradovate App Secret", type="password")
            
            # Add Rithmic API settings
            st.markdown("#### Rithmic")
            st.checkbox("Enable Rithmic API", value=False)
            rithmic_user = st.text_input("Rithmic Username")
            rithmic_password = st.text_input("Rithmic Password", type="password")
            rithmic_app_key = st.text_input("Rithmic App Key", type="password")
            
            # CSV data settings
            st.markdown("#### CSV Data")
            csv_directory = st.text_input("CSV Directory", value="./data/csv")
            st.checkbox("Automatically detect CSV format", value=True)
            
            # Save settings button
            st.button("Save Data Settings")
            
        with settings_tabs[2]:
            st.markdown("### Visualization Settings")
            
            # Chart settings
            chart_type = st.selectbox(
                "Default Chart Type",
                ["Candlestick", "OHLC", "Line", "Area"],
                index=0
            )
            
            # Chart colors
            st.subheader("Chart Colors")
            bull_color = st.color_picker("Bullish Candle Color", value="#26A69A")
            bear_color = st.color_picker("Bearish Candle Color", value="#EF5350")
            ema_color = st.color_picker("EMA Line Color", value="#2196F3")
            
            # Indicator settings
            st.subheader("Indicators")
            st.checkbox("Show volume", value=True)
            st.checkbox("Show EMA", value=True)
            st.checkbox("Show trade markers", value=True)
            st.checkbox("Show equity curve", value=True)
            
            # Save settings button
            st.button("Save Visualization Settings")
            
        with settings_tabs[3]:
            st.markdown("### Export Settings")
            
            # Report format
            report_format = st.selectbox(
                "Report Format",
                ["HTML", "PDF", "Excel", "CSV", "JSON"],
                index=0
            )
            
            # Report content
            st.subheader("Report Content")
            st.checkbox("Include performance metrics", value=True)
            st.checkbox("Include trade list", value=True)
            st.checkbox("Include charts", value=True)
            st.checkbox("Include strategy parameters", value=True)
            
            # Export directory
            export_dir = st.text_input("Export Directory", value="./reports")
            
            # Generate sample report button
            st.button("Generate Sample Report")

if __name__ == "__main__":
    main()
