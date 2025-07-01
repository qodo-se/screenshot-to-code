# Screenshot to Code Application Flowchart

The diagram below illustrates the complete flow of the screenshot-to-code application, from input selection through code generation to the final output.

```mermaid
flowchart TD
    Start([Start]) --> Initial[Initial State]
    Initial --> InputChoice{Input Choice}
    
    InputChoice -->|Image Upload| UploadImage[Upload Reference Image]
    InputChoice -->|Video| UploadVideo[Upload Video]
    InputChoice -->|Import from Code| ImportCode[Import from Code]
    
    UploadImage --> SetInputMode[Set Input Mode]
    UploadVideo --> SetInputMode
    ImportCode --> SetIsImportedFromCode[Set IsImportedFromCode]
    
    SetInputMode --> ValidateInput{Valid Input?}
    SetIsImportedFromCode --> ValidateInput
    
    ValidateInput -->|No| Initial
    ValidateInput -->|Yes| SetReferenceImages[Set Reference Images]
    
    SetReferenceImages --> DoCreate[doCreate Function]
    DoCreate --> DoGenerateCode[doGenerateCode Function]
    
    DoGenerateCode --> ResetConsole[Reset Execution Console]
    ResetConsole --> SetAppState[Set AppState to CODING]
    SetAppState --> CreateCommit[Create New Commit]
    CreateCommit --> AddCommit[Add Commit to Store]
    AddCommit --> SetHead[Set Head to New Commit]
    
    SetHead --> GenerateCode[Generate Code Process]
    
    GenerateCode -->|Tokens| AppendCode[Append Commit Code]
    GenerateCode -->|Status Updates| UpdateConsole[Update Execution Console]
    
    GenerateCode -->|Complete| CodeReady[Set AppState to CODE_READY]
    GenerateCode -->|Cancel| CancelGeneration[Cancel Code Generation]
    
    CancelGeneration --> Initial
    
    CodeReady --> ViewResult[View Generated Code]
    ViewResult --> EditOptions{Edit Options}
    
    EditOptions -->|Regenerate| Regenerate[Regenerate Code]
    EditOptions -->|Update| UpdateCode[Update with New Instructions]
    EditOptions -->|Reset| ResetApp[Reset App]
    EditOptions -->|Select & Edit| SelectEdit[Enter Select & Edit Mode]
    
    Regenerate --> DoGenerateCode
    UpdateCode --> SetUpdateInstruction[Set Update Instruction]
    SetUpdateInstruction --> DoGenerateCode
    ResetApp --> ResetCommits[Reset Commits]
    ResetCommits --> ResetHead[Reset Head]
    ResetHead --> Initial
    
    SelectEdit --> ToggleSelectEditMode[Toggle inSelectAndEditMode]
    ToggleSelectEditMode --> EditCode[Edit Code Manually]
    EditCode --> SaveChanges[Save Changes]
    SaveChanges --> ViewResult
    
    subgraph States
        direction LR
        AppStateInitial[AppState.INITIAL]
        AppStateCoding[AppState.CODING]
        AppStateCodeReady[AppState.CODE_READY]
    end
    
    subgraph Stores
        direction LR
        ProjectStore[Project Store
        - commits
        - head
        - referenceImages
        - executionConsoles]
        AppStore[App Store
        - appState
        - updateInstruction
        - inSelectAndEditMode]
        SettingsStore[Settings Store
        - API keys
        - model selection
        - editorTheme
        - generatedCodeConfig]
    end
    
    subgraph CommitStructure
        direction TB
        Commit[Commit Object]
        Commit --> Hash[hash]
        Commit --> Type[type: ai_create/ai_edit]
        Commit --> ParentHash[parentHash]
        Commit --> Inputs[inputs]
        Commit --> Variants[variants array]
        Variants --> Code[code]
    end
```

## Key Components

1. **Input Selection**:
   - Image upload
   - Video upload/recording
   - Import from existing code

2. **Code Generation Process**:
   - Input validation
   - Commit creation
   - Code generation with real-time updates
   - Execution console updates

3. **State Management**:
   - INITIAL: Ready for input
   - CODING: Generating code
   - CODE_READY: Code generation complete

4. **User Actions**:
   - View generated code
   - Regenerate code
   - Update with new instructions
   - Select and edit mode
   - Reset application

5. **Data Stores**:
   - Project Store: Manages commits, head pointer, reference images, and execution consoles
   - App Store: Manages application state, update instructions, and select/edit mode
   - Settings Store: Manages API keys, model selection, editor theme, and code configuration