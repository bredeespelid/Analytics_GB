# Last inn nødvendig bibliotek
library(jsonlite)
library(dplyr)
library(ggplot2)
library(lubridate)
library(tidyr)

# Les JSON-filen
# Erstatt 'path/to/your/file.json' med den faktiske filbanen til din JSON-fil
data <- fromJSON('Processed_Google_ratings_positive.json', simplifyVector = TRUE)

# Konverter data til en tibble (dataframe)
data <- as_tibble(data)

# Vis de første radene i datasettet
head(data)

# Vis strukturen til datasettet
str(data)

# Hvis 'categories' er en liste-kolonne, kan du konvertere den til separate kolonner
data <- data %>%
  mutate(across(where(is.list), as.data.frame),
         Dato = ymd(substr(Dato, 1, 10))) %>% 
  unnest_wider(categories) %>% 
  rename(
    Positiv = `God kundeservice/opplevelse`,
    Rimelige_P = `Rimelige produkter`,
    Gode_P = `Gode produkter`,
    Kort_V = `Kort kø/ventetid`,
    Godt_R = `Godt renhold`,
    Kommentar = `Ingen kommentar`,
    Annet_B = `Annet Bra`,
    Rating = `★`
  ) %>% 
  filter(Dato > '2019-12-31',
         Dato < '2025-01-01',
         Avd != "16 EV")


# Test_2 ------------------------------------------------------------------

# Funksjon for å lage gyldig formel med forklaringsgrad
generate_valid_formula <- function(department_data) {
  # Bygg lineær modell
  model <- lm(Rating ~ Positiv + Rimelige_P + Gode_P + Kort_V + Godt_R + Annet_B, 
              data = department_data)
  
  # Hent modellresultater og filtrer kun signifikante variabler
  coefficients <- broom::tidy(model) %>%
    filter(p.value < 0.1) %>%
    select(term, estimate)
  
  # Beregn forklaringsgrad (R^2)
  model_summary <- summary(model)
  r_squared <- model_summary$r.squared
  
  # Hvis ingen signifikante variabler finnes, returner konstantledd med R^2
  if (nrow(coefficients) == 0) {
    intercept <- mean(department_data$Rating, na.rm = TRUE)
    return(list(
      Formel = paste0("Rating = ", sprintf("%.3f", intercept)),
      Forklaringsgrad = sprintf("%.3f", r_squared)
    ))
  }
  
  # Hent konstantleddet (Intercept)
  intercept <- coefficients %>% filter(term == "(Intercept)") %>% pull(estimate)
  
  # Hvis konstantleddet mangler, bruk gjennomsnittet som konstantledd
  if (length(intercept) == 0) {
    intercept <- mean(department_data$Rating, na.rm = TRUE)
  }
  
  # Legg til signifikante prediktorer
  predictors <- coefficients %>%
    filter(term != "(Intercept)") %>%
    mutate(term = gsub("`", "", term)) %>%
    mutate(formula_segment = paste0(sprintf("%.3f", estimate), term)) %>%
    pull(formula_segment)
  
  # Lag formelstrengen
  formula_string <- paste0("Rating = ", sprintf("%.3f", intercept))
  if (length(predictors) > 0) {
    formula_string <- paste0(formula_string, " + ", paste(predictors, collapse = " + "))
  }
  
  return(list(Formel = formula_string, Forklaringsgrad = sprintf("%.3f", r_squared)))
}

# Generer formler og forklaringsgrad for hver avdeling
formulas <- data %>%
  group_by(Avd) %>%
  group_map(~ generate_valid_formula(.x), .keep = TRUE) %>%
  setNames(unique(data$Avd))

# Lag en dataframe med forklaringsgrad og formler
formulas_df <- tibble(
  Avdeling = names(formulas),
  Formel = sapply(formulas, function(x) x$Formel),
  Forklaringsgrad = sapply(formulas, function(x) x$Forklaringsgrad)
)

# Fjern NA-resultater (ugyldige modeller)
formulas_df <- formulas_df %>%
  filter(!is.na(Formel))

# Vis formler med forklaringsgrad
print(formulas_df, n = Inf)

# Lagre resultatene i en CSV-fil
write.csv(formulas_df, "formler_positive.csv", row.names = FALSE)


# Last inn nødvendige bibliotek
library(dplyr)
library(ggplot2)
library(broom)

# Utforsk distribusjonen av Kort_V
kort_v_dist <- data %>%
  summarise(
    Antall_Kort_V_0 = sum(Kort_V == 0, na.rm = TRUE),
    Antall_Kort_V_1 = sum(Kort_V == 1, na.rm = TRUE),
    Andel_Kort_V_1 = mean(Kort_V == 1, na.rm = TRUE)
  )
print(kort_v_dist)

# Utfør korrelasjonsanalyse for binære variabler
cor_matrix <- data %>%
  select(Positiv, Rimelige_P, Gode_P, Kort_V, Godt_R, Annet_B, Rating) %>%
  cor(use = "complete.obs")
print(cor_matrix)

# Visualiser effekten av Kort_V på Rating
ggplot(data, aes(x = Kort_V, y = Rating)) +
  geom_boxplot() +
  labs(title = "Effekt av Kort Ventetid (Kort_V) på Rating", x = "Kort Ventetid (1 = Kort, 0 = Lang)", y = "Rating")

# Kjør en enkel lineær modell for Kort_V alene
kort_v_model <- lm(Rating ~ Kort_V, data = data)
summary(kort_v_model)

# Utforsk Kort_V på tvers av avdelinger
kort_v_avdeling <- data %>%
  group_by(Avd, Kort_V) %>%
  summarise(Gjennomsnitt_Rating = mean(Rating, na.rm = TRUE), .groups = "drop") %>%
  arrange(desc(Gjennomsnitt_Rating))
print(kort_v_avdeling)

# Kjør en lineær modell med alle variabler inkludert
full_model <- lm(Rating ~ Positiv + Rimelige_P + Gode_P + Kort_V + Godt_R + Annet_B, data = data)
summary(full_model)

# Identifiser signifikante prediktorer
signifikante_prediktorer <- tidy(full_model) %>%
  filter(p.value < 0.1)
print(signifikante_prediktorer)

# Visualiser residualer for modellen
ggplot(data.frame(residuals = resid(full_model), fitted = fitted(full_model)), aes(x = fitted, y = residuals)) +
  geom_point() +
  labs(title = "Residualanalyse for Full Modell", x = "Fitted Values", y = "Residuals") +
  geom_hline(yintercept = 0, linetype = "dashed")

# Test for multikollinearitet med Variance Inflation Factor (VIF)
library(car)
vif_values <- vif(full_model)
print(vif_values)


