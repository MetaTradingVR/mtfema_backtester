# Custom Indicators Dashboard Integration Plan

## Overview

This document outlines the plan for integrating custom indicators functionality into the MT9 EMA Dashboard interface, making it easier for traders to create, manage, and use custom indicators without writing Python code.

## Dashboard Component Design

### 1. Custom Indicators Management Page

**Path:** `/indicators`

**Features:**
- List all available indicators (built-in and custom)
- Create new custom indicators through a visual interface
- Edit or delete existing custom indicators
- Import/export indicators as JSON configurations

### 2. Indicator Builder Component

**Component:** `<IndicatorBuilder />`

![Indicator Builder Mockup](https://via.placeholder.com/800x600.png?text=Indicator+Builder+Mockup)

**Features:**
- Drag-and-drop formula builder
- Common mathematical operations (+, -, *, /, etc.)
- Technical analysis functions (SMA, EMA, ATR, etc.)
- Input parameter configuration
- Real-time preview of indicator values on a chart
- Formula validation
- Save/load indicator definitions

### 3. Backtesting Integration

**Component:** `<BacktestConfigForm />`

**Enhanced Features:**
- Select custom indicators for visualization during backtesting
- Include custom indicator values in backtest reports
- Use custom indicators for signal generation through a rules engine

### 4. Strategy Builder Integration

**Component:** `<StrategyBuilder />`

**Features:**
- Rules engine for creating strategies using custom indicators
- Visual condition builder (e.g., "When indicator X crosses above/below indicator Y")
- Entry/exit rule configuration based on indicator values
- Risk management configuration

## API Endpoints

Add the following endpoints to the backend API:

1. **List Indicators**
   - `GET /api/indicators` - List all available indicators
   
2. **Manage Custom Indicators**
   - `POST /api/indicators` - Create a new custom indicator
   - `GET /api/indicators/{indicator_id}` - Get indicator details
   - `PUT /api/indicators/{indicator_id}` - Update an indicator
   - `DELETE /api/indicators/{indicator_id}` - Delete an indicator
   
3. **Test Indicators**
   - `POST /api/indicators/test` - Test an indicator formula on sample data
   
4. **Export/Import**
   - `GET /api/indicators/export` - Export indicators as JSON
   - `POST /api/indicators/import` - Import indicators from JSON

## Backend Implementation

### 1. Indicator Registry API

Create a REST API wrapper around the existing `IndicatorRegistry` class:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from mtfema_backtester.utils.indicators import get_indicator_registry

router = APIRouter()
registry = get_indicator_registry()

class IndicatorSchema(BaseModel):
    name: str
    formula: str
    parameters: dict

@router.get("/indicators")
async def list_indicators():
    return {"indicators": registry.list_indicators()}

@router.post("/indicators")
async def create_indicator(indicator: IndicatorSchema):
    # Logic to create indicator from formula
    # ...
    return {"message": "Indicator created", "id": new_id}
```

### 2. Formula Parser

Implement a formula parser that converts user-defined formulas into actual indicator calculations:

```python
class FormulaParser:
    def __init__(self, formula, parameters):
        self.formula = formula
        self.parameters = parameters
        
    def generate_calculation_function(self):
        # Parse the formula and generate a calculation function
        # ...
        return calculation_function
```

### 3. Dynamic Indicator Creation

Create a system for dynamically generating and registering indicators based on user formulas:

```python
class DynamicIndicator(Indicator):
    def __init__(self, calc_function, params, name=None):
        self.calc_function = calc_function
        super().__init__(name, params)
    
    def _calculate(self, data):
        return self.calc_function(data, self.params)
```

## Implementation Steps

1. **Phase 1: Backend API**
   - Implement indicator management API endpoints
   - Create formula parser for simple formulas
   - Build dynamic indicator registration

2. **Phase 2: Dashboard UI**
   - Create indicator management page
   - Implement basic indicator builder component
   - Add indicator selection to backtest configuration

3. **Phase 3: Advanced Features**
   - Implement drag-and-drop formula builder
   - Add strategy rules engine
   - Create indicator library sharing functionality

4. **Phase 4: Testing & Documentation**
   - Create comprehensive user guide
   - Develop tutorial videos
   - Conduct user testing

## Timeline

- **Phase 1:** 2-3 weeks
- **Phase 2:** 3-4 weeks
- **Phase 3:** 4-6 weeks
- **Phase 4:** 2-3 weeks

**Total estimated time:** 11-16 weeks
