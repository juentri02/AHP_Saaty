# app/services/ahp_math.py
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple

class AHPMathEngine:
    """
    Core Mathematical Engine for Saaty's Analytic Hierarchy Process (AHP).
    Handles Pairwise Comparisons, Eigenvector calculations, CI, and CR.
    """
    
    # Random Index (RI) table based on Saaty's standard values
    # Size (n):  1    2    3     4     5     6     7     8     9    10
    RI_DICT = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

    @staticmethod
    def create_pairwise_matrix(criteria: List[str], comparisons: Dict[Tuple[str, str], float]) -> pd.DataFrame:
        """
        Creates a pairwise comparison matrix from a list of criteria and their comparison values.
        Comparisons dictate how much more important criterion A is over criterion B.
        """
        n = len(criteria)
        matrix = np.ones((n, n)) # Initialize with 1s on the diagonal
        
        for i, crit_row in enumerate(criteria):
            for j, crit_col in enumerate(criteria):
                if i == j:
                    continue
                # Check if we have a defined comparison
                if (crit_row, crit_col) in comparisons:
                    val = comparisons[(crit_row, crit_col)]
                    matrix[i, j] = val
                    matrix[j, i] = 1.0 / val # Reciprocal rule
                elif (crit_col, crit_row) in comparisons:
                    val = comparisons[(crit_col, crit_row)]
                    matrix[i, j] = 1.0 / val
                    matrix[j, i] = val
                    
        return pd.DataFrame(matrix, index=criteria, columns=criteria)

    @staticmethod
    def calculate_eigenvector(matrix: pd.DataFrame) -> pd.Series:
        """
        Calculates the normalized Eigenvector (Priority Weights).
        Step 1: Sum the columns
        Step 2: Divide each element by its column sum (Normalization)
        Step 3: Average the rows
        """
        # 1. Sum each column
        col_sums = matrix.sum(axis=0)
        
        # 2. Normalize the matrix
        normalized_matrix = matrix.div(col_sums, axis=1)
        
        # 3. Calculate average of each row (This is the Priority Weight / Eigenvector)
        eigenvector = normalized_matrix.mean(axis=1)
        return eigenvector

    @staticmethod
    def check_consistency(matrix: pd.DataFrame, eigenvector: pd.Series) -> Tuple[float, float, bool]:
        """
        Calculates Lambda Max, Consistency Index (CI), and Consistency Ratio (CR).
        Returns (CI, CR, is_consistent)
        """
        n = len(matrix)
        if n <= 2:
            return 0.0, 0.0, True # Matrices of size 1 or 2 are always consistent

        # 1. Calculate Weighted Sum Vector (Matrix * Eigenvector)
        weighted_sum_vector = matrix.dot(eigenvector)
        
        # 2. Calculate Eigenvalue (Lambda) for each row
        eigenvalues = weighted_sum_vector / eigenvector
        
        # 3. Calculate Lambda Max (Average of Eigenvalues)
        lambda_max = eigenvalues.mean()
        
        # 4. Calculate Consistency Index (CI)
        ci = (lambda_max - n) / (n - 1)
        
        # 5. Calculate Consistency Ratio (CR)
        ri = AHPMathEngine.RI_DICT.get(n, 1.49) # Default to 1.49 if n > 10 (rare)
        cr = ci / ri if ri != 0 else 0.0
        
        # Consistent if CR <= 0.1
        is_consistent = cr <= 0.1
        
        return ci, cr, is_consistent

# Initialize as singleton if needed, though methods are static
ahp_math = AHPMathEngine()