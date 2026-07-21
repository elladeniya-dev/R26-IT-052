class ApiConstants {
  // Local development URL
  static const String baseUrl = "http://192.168.8.100:8000";

  // Outfit Compatibility API endpoint
  static const String generateOutfitsEndpoint = "$baseUrl/outfits/generate";

  // Saved Outfit API endpoints
  static String saveOutfitEndpoint(String outfitId) {
    return "$baseUrl/saved-outfits/save/$outfitId";
  }

  static String getSavedOutfitsEndpoint(String userId) {
    return "$baseUrl/saved-outfits/$userId";
  }

  static String savedOutfitDetailEndpoint(String outfitId) {
    return "$baseUrl/saved-outfits/detail/$outfitId";
  }

  static String removeSavedOutfitEndpoint(String outfitId) {
    return "$baseUrl/saved-outfits/$outfitId";
  }
}
